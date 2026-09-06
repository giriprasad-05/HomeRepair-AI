"""
History Matching Service — deterministic similarity check.

Compares current issue against past closed/resolved issues on the same appliance.
Uses keyword overlap on title, description, and symptom terms.
Does NOT use an LLM for matching.
"""
from typing import Any, Dict, List, Optional
import re
from sqlalchemy.orm import Session

from app.models.issue import IssueReport
from app.models.repair import RepairHistory
from app.models.enums import IssueStatus, RepairOutcome


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_HIGH_CONFIDENCE_THRESHOLD = 0.60   # ≥ 60% keyword overlap → strong match
_MEDIUM_CONFIDENCE_THRESHOLD = 0.35  # ≥ 35% → weak / partial match
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
    "of", "and", "or", "for", "with", "has", "had", "it", "this", "that",
    "be", "by", "from", "as", "not", "my", "our", "its", "does", "do",
    "not", "no", "just", "but", "so", "if", "then"
}


def _tokenise(text: str) -> set:
    """Lowercase, split, strip punctuation, remove stop-words."""
    words = re.split(r"[\s,;.!?/\-_]+", (text or "").lower())
    return {w for w in words if len(w) >= 3 and w not in _STOP_WORDS}


def _issue_tokens(issue: IssueReport) -> set:
    """Combine title + description + symptom values into a single token set."""
    tokens = _tokenise(issue.title or "")
    tokens |= _tokenise(issue.description or "")
    for symptom in (issue.symptoms or []):
        tokens |= _tokenise(symptom.name or "")
        tokens |= _tokenise(symptom.value or "")
    return tokens


def _overlap_ratio(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _is_closed(issue: IssueReport) -> bool:
    return issue.status in (IssueStatus.RESOLVED, IssueStatus.FAILED)


def _map_confidence(ratio: float) -> str:
    if ratio >= _HIGH_CONFIDENCE_THRESHOLD:
        return "high"
    if ratio >= _MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    return "low"


def _calculate_similarity(past: IssueReport, current: IssueReport) -> float:
    """
    Multi-signal similarity calculation:
    - Title tokens (weight 50%): Dice overlap + containment
    - Symptoms tokens (weight 30%): overlap of symptom names and values
    - Overall tokens (weight 20%): Dice overlap on full issue token sets
    """
    # 1. Title similarity
    past_title = _tokenise(past.title or "")
    curr_title = _tokenise(current.title or "")
    if not past_title or not curr_title:
        title_sim = 0.0
    else:
        overlap = len(past_title & curr_title)
        dice = (2.0 * overlap) / (len(past_title) + len(curr_title))
        containment = overlap / min(len(past_title), len(curr_title))
        title_sim = max(dice, containment * 0.90)

    # 2. Symptoms similarity
    past_symp = set()
    for s in (past.symptoms or []):
        past_symp |= _tokenise(s.name or "")
        past_symp |= _tokenise(s.value or "")
    curr_symp = set()
    for s in (current.symptoms or []):
        curr_symp |= _tokenise(s.name or "")
        curr_symp |= _tokenise(s.value or "")

    if past_symp and curr_symp:
        overlap_s = len(past_symp & curr_symp)
        symp_sim = (2.0 * overlap_s) / (len(past_symp) + len(curr_symp))
    else:
        # If symptoms are absent in either past or current issue, fall back to title similarity
        # so missing symptoms never penalize or prevent historical matching
        symp_sim = title_sim

    # 3. Overall tokens Dice similarity
    past_all = _issue_tokens(past)
    curr_all = _issue_tokens(current)
    all_dice = (2.0 * len(past_all & curr_all)) / (len(past_all) + len(curr_all)) if (past_all and curr_all) else 0.0

    score = 0.50 * title_sim + 0.30 * symp_sim + 0.20 * all_dice
    return min(1.0, round(score, 3))


def _has_new_error_codes(past: IssueReport, current: IssueReport) -> bool:
    """Return True if current issue has an error code that the past issue did not have."""
    past_codes = {
        s.value.strip().upper()
        for s in (past.symptoms or [])
        if "error" in (s.name or "").lower() or "code" in (s.name or "").lower()
    }
    current_codes = {
        s.value.strip().upper()
        for s in (current.symptoms or [])
        if "error" in (s.name or "").lower() or "code" in (s.name or "").lower()
    }
    if current_codes and not current_codes.issubset(past_codes):
        return True
    return False


def _should_reinvestigate(past: IssueReport, current: IssueReport, score: float, outcome_str: Optional[str] = None) -> bool:
    """
    Reinvestigation needed when:
    - Previous repair explicitly FAILED or was PARTIALLY_RESOLVED
    - No outcome was ever recorded (diagnosis but no repair follow-up)
    - Confidence is borderline (< 60%)
    - Current issue introduces a new error code
    """
    outcome = outcome_str or (past.repair_outcome.value if past.repair_outcome else None)
    if outcome in ("failed", "partially_resolved", RepairOutcome.FAILED.value, RepairOutcome.PARTIALLY_RESOLVED.value):
        return True
    if outcome is None and past.diagnosis_result:
        # Diagnosed but no repair outcome recorded -> weak evidence
        return True
    if score < _HIGH_CONFIDENCE_THRESHOLD:
        return True
    if _has_new_error_codes(past, current):
        return True
    return False


def _no_match(reason: str) -> Dict[str, Any]:
    return {
        "match_found": False,
        "matched_issue_id": None,
        "similarity_reason": reason,
        "previous_diagnosis": None,
        "previous_repair": None,
        "previous_outcome": None,
        "confidence": "low",
        "similarity_score": 0.0,
        "trigger_reinvestigation": False,
        "analysis_mode": "fresh_investigation",
    }


def _extract_diagnosis_summary(issue: IssueReport) -> Optional[str]:
    """Pull a short diagnosis summary from stored diagnosis_result JSON."""
    if not issue.diagnosis_result:
        return None
    try:
        import json
        data = json.loads(issue.diagnosis_result)
        return data.get("summary") or data.get("recommended_next_step")
    except Exception:
        return str(issue.diagnosis_result)[:300]


def find_history_match(
    db: Session,
    appliance_id: int,
    current_issue: IssueReport,
) -> Dict[str, Any]:
    """
    Compare current_issue against ALL past issues on the same appliance.

    Returns structured data for the agent to decide next actions:
    match_found, matched_issue_id, similarity_reason, previous_diagnosis,
    previous_repair, previous_outcome, confidence, similarity_score,
    trigger_reinvestigation, analysis_mode.
    """
    past_issues: List[IssueReport] = (
        db.query(IssueReport)
        .filter(
            IssueReport.appliance_id == appliance_id,
            IssueReport.id != current_issue.id,
        )
        .all()
    )

    if not past_issues:
        return _no_match("No previous issues on record for this appliance.")

    current_tokens = _issue_tokens(current_issue)
    if not current_tokens:
        return _no_match("Current issue has no meaningful tokens to compare.")

    best_score = 0.0
    best_issue: Optional[IssueReport] = None

    for past in past_issues:
        score = _calculate_similarity(past, current_issue)
        if score > best_score:
            best_score = score
            best_issue = past

    if best_score < _MEDIUM_CONFIDENCE_THRESHOLD or best_issue is None:
        return _no_match(
            f"No sufficiently similar previous problem found (best score: {best_score:.2f})."
        )

    confidence = _map_confidence(best_score)
    previous_diagnosis = _extract_diagnosis_summary(best_issue)
    previous_outcome = best_issue.repair_outcome.value if best_issue.repair_outcome else None
    previous_repair = best_issue.repair_notes or None

    if not previous_outcome:
        latest_repair = (
            db.query(RepairHistory)
            .filter(RepairHistory.issue_id == best_issue.id)
            .order_by(RepairHistory.id.desc())
            .first()
        )
        if latest_repair and latest_repair.outcome:
            previous_outcome = str(latest_repair.outcome).lower()
            if not previous_repair:
                previous_repair = latest_repair.notes or latest_repair.description

    trigger_reinvestigation = _should_reinvestigate(best_issue, current_issue, best_score, previous_outcome)

    if trigger_reinvestigation:
        analysis_mode = "reinvestigation_required"
        reason = (
            f"Similar issue found (score={best_score:.0%}) but previous repair "
            f"outcome was '{previous_outcome or 'unknown'}' — reinvestigation required."
        )
    else:
        analysis_mode = "historical_match"
        reason = (
            f"Similar issue found (score={best_score:.0%}). "
            f"Previous outcome: '{previous_outcome or 'successful'}' — reusing historical knowledge."
        )

    return {
        "match_found": True,
        "matched_issue_id": best_issue.id,
        "similarity_reason": reason,
        "previous_diagnosis": previous_diagnosis,
        "previous_repair": previous_repair,
        "previous_outcome": previous_outcome,
        "confidence": confidence,
        "similarity_score": round(best_score, 3),
        "trigger_reinvestigation": trigger_reinvestigation,
        "analysis_mode": analysis_mode,
    }
