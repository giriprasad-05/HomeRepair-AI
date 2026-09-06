"""
LangGraph node functions for HomeRepair AI diagnostic agent.

Each node:
  - Receives AgentState
  - Returns a dict of updated state keys (LangGraph merges them)
  - Never exposes chain-of-thought or system prompts
  - Handles failures gracefully without crashing the graph

Workflow:
  validate_issue
  → load_appliance_context
  → retrieve_memories
  → check_history_match          ← NEW: deterministic before any tool analysis
  → decide_investigation_mode    ← NEW: routes based on match result
      HISTORICAL_MATCH → finalize (skip tools) with "reused previous knowledge"
      INSUFFICIENT_DATA → finalize immediately with targeted questions
      FRESH or REINVESTIGATION → continue tool analysis
  → analyze_history
  → analyze_symptoms
  → analyze_warranty
  → analyze_repairs
  → [conditional] manual_lookup_node (only when error codes present)
  → generate_hypotheses
  → evaluate_evidence
  → [conditional] llm_synthesis (only when evidence is sufficient)
  → store_memory
  → finalize_result
"""
import re
import json
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.models.appliance import Appliance
from app.models.issue import IssueReport
from app.models.symptom import Symptom
from app.models.enums import MemoryType
from app.tools.appliance_history_tool import get_appliance_history
from app.tools.symptom_pattern_tool import analyze_symptom_patterns
from app.tools.repair_outcome_tool import analyze_repair_outcomes
from app.tools.warranty_tool import check_warranty_status
from app.tools.manual_lookup_tool import lookup_error_code
from app.services.memory_service import (
    get_relevant_memories,
    store_memory,
    check_duplicate_memory,
)
from app.services.history_matching_service import find_history_match
from app.agent.llm import get_llm


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _safe_dict(obj: Any) -> Dict:
    """Convert a SQLAlchemy model to a plain dict for state storage."""
    if obj is None:
        return {}
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return dict(obj)


def _extract_error_codes(symptoms: List[Any]) -> List[str]:
    """Detect error-code-like values in symptom list (e.g. E1, F7E1, UE)."""
    error_pattern = re.compile(r"^([A-Z]{1,2}\d{1,2}([A-Z]\d{1,2})?|\d{1,2}[A-Z]{1,2}|[A-Z]{2,3})$", re.IGNORECASE)
    codes = []
    for s in symptoms:
        name = getattr(s, "name", "") or ""
        value = getattr(s, "value", "") or ""
        if ("error" in name.lower() or "code" in name.lower()) and value.strip():
            codes.append(value.strip().lower())
            continue
        for text in [name, value]:
            if error_pattern.match(text.strip()):
                codes.append(text.strip().lower())
    return codes


# ---------------------------------------------------------------------------
# NODE: Validate Issue
# ---------------------------------------------------------------------------

def validate_issue_node(state: AgentState, db: Session) -> Dict:
    """
    Verify issue and appliance exist.
    Hard stop on failure — populates errors and final_result to abort.
    """
    issue_id = state.get("issue_id")
    if not issue_id:
        return {
            "errors": ["No issue_id provided."],
            "final_result": {"error": "No issue_id provided.", "activity_log": []},
        }

    issue: IssueReport = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not issue:
        return {
            "errors": [f"Issue {issue_id} not found."],
            "final_result": {
                "error": f"Issue {issue_id} not found.",
                "activity_log": [],
            },
        }

    appliance: Appliance = (
        db.query(Appliance).filter(Appliance.id == issue.appliance_id).first()
    )
    if not appliance:
        return {
            "errors": [f"Appliance {issue.appliance_id} not found."],
            "final_result": {
                "error": f"Appliance {issue.appliance_id} not found.",
                "activity_log": [],
            },
        }

    return {
        "appliance_id": issue.appliance_id,
        "activity_log": (state.get("activity_log") or []) + ["Validated issue and appliance."],
        "errors": [],
    }


# ---------------------------------------------------------------------------
# NODE: Load Appliance Context
# ---------------------------------------------------------------------------

def load_appliance_context_node(state: AgentState, db: Session) -> Dict:
    """Load appliance and issue details from the database."""
    issue_id = state["issue_id"]
    appliance_id = state["appliance_id"]

    issue: IssueReport = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    db.refresh(issue)
    appliance: Appliance = db.query(Appliance).filter(Appliance.id == appliance_id).first()

    symptoms_list = db.query(Symptom).filter(Symptom.issue_id == issue_id).all()

    issue_ctx = {
        "id": issue.id,
        "title": issue.title,
        "description": issue.description,
        "severity": issue.severity.value if issue.severity else None,
        "status": issue.status.value if issue.status else None,
        "reported_at": str(issue.reported_at),
        "symptoms": [
            {"name": s.name, "value": s.value, "unit": s.unit}
            for s in symptoms_list
        ],
    }

    appliance_ctx = {
        "id": appliance.id,
        "name": appliance.name,
        "brand": appliance.brand,
        "model_number": appliance.model_number,
        "category": appliance.category.value if appliance.category else None,
        "location": appliance.location,
        "purchase_date": str(appliance.purchase_date) if appliance.purchase_date else None,
        "warranty_expiry": str(appliance.warranty_expiry) if appliance.warranty_expiry else None,
    }

    # Detect error codes for conditional routing
    has_error_codes = bool(_extract_error_codes(symptoms_list))

    log = (state.get("activity_log") or []) + ["Loaded appliance and issue context."]
    return {
        "issue_context": issue_ctx,
        "appliance_context": appliance_ctx,
        "_has_error_codes": has_error_codes,
        "activity_log": log,
    }


# ---------------------------------------------------------------------------
# NODE: Retrieve Memories
# ---------------------------------------------------------------------------

def retrieve_memories_node(state: AgentState, db: Session) -> Dict:
    """Fetch relevant long-term memories for this appliance."""
    appliance_id = state["appliance_id"]
    try:
        memories = get_relevant_memories(db, appliance_id, limit=8)
        mem_list = [
            {
                "type": m.memory_type.value,
                "content": m.content,
                "importance": m.importance_score,
            }
            for m in memories
        ]
    except Exception as e:
        mem_list = []
        state.get("errors", []).append(f"Memory retrieval error: {e}")

    log = (state.get("activity_log") or []) + ["Retrieved appliance memory."]
    return {"memories": mem_list, "activity_log": log}


# ---------------------------------------------------------------------------
# NODE: Check History Match  ← NEW
# ---------------------------------------------------------------------------

def check_history_match_node(state: AgentState, db: Session) -> Dict:
    """
    Deterministic check: does this appliance have a sufficiently similar
    prior issue with a resolved/recorded outcome?

    This runs BEFORE any tool analysis or LLM call, so we can decide whether
    to reuse past knowledge or perform a fresh investigation.
    """
    issue_id = state["issue_id"]
    appliance_id = state["appliance_id"]

    issue: IssueReport = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not issue:
        return {
            "history_match": {"match_found": False, "analysis_mode": "fresh_investigation"},
            "analysis_mode": "fresh_investigation",
            "activity_log": (state.get("activity_log") or []) + ["No prior history to compare."],
        }

    match_result = find_history_match(db, appliance_id, issue)

    mode = match_result.get("analysis_mode", "fresh_investigation")
    log_msgs = {
        "historical_match": "Checked appliance history — previous successful repair found.",
        "reinvestigation_required": "Checked appliance history — previous repair was incomplete, reinvestigation needed.",
        "fresh_investigation": "Checked appliance history — no similar previous issue found.",
        "insufficient_data": "Insufficient symptom data for history comparison.",
    }
    log_msg = log_msgs.get(mode, "Compared previous incidents.")

    return {
        "history_match": match_result,
        "analysis_mode": mode,
        "activity_log": (state.get("activity_log") or []) + [log_msg],
    }


# ---------------------------------------------------------------------------
# NODE: Decide Investigation Mode  ← NEW
# ---------------------------------------------------------------------------

def decide_investigation_mode_node(state: AgentState, db: Session) -> Dict:
    """
    Based on history match, decide:
    - HISTORICAL_MATCH → skip full tool analysis, summarise from history
    - REINVESTIGATION / FRESH → continue tool analysis
    - INSUFFICIENT_DATA → early exit with targeted questions

    Sets _skip_full_investigation flag for graph routing.
    """
    mode = state.get("analysis_mode", "fresh_investigation")
    issue_ctx = state.get("issue_context") or {}
    symptoms = issue_ctx.get("symptoms", [])

    # Check for genuinely insufficient data (e.g. title has no substance and no description)
    title = (issue_ctx.get("title") or "").strip().lower()
    description = (issue_ctx.get("description") or "").strip().lower()
    if description in {"none", "n/a", "no description", "unknown", ""}:
        effective_desc = ""
    else:
        effective_desc = description

    # The agent should only return INSUFFICIENT_DATA when the overall information is genuinely insufficient
    is_too_vague = (
        (not effective_desc and (len(title) < 12 or "vague" in title or title in {"machine is not working", "not working", "broken", "issue", "problem"}))
        or len(f"{title} {effective_desc}".strip()) < 5
        or f"{title} {effective_desc}".strip() in {"broken", "problem", "issue", "not working", "machine is not working"}
    )

    if is_too_vague:
        mode = "insufficient_data"

    skip = (mode == "historical_match")

    activity = state.get("activity_log") or []
    mode_descriptions = {
        "historical_match": "Decision: HISTORICAL MATCH — reusing relevant previous knowledge.",
        "reinvestigation_required": "Decision: REINVESTIGATION — previous repair was incomplete.",
        "fresh_investigation": "Decision: FRESH INVESTIGATION — no prior similar issue.",
        "insufficient_data": "Decision: INSUFFICIENT DATA — targeted questions required.",
    }
    activity = activity + [mode_descriptions.get(mode, f"Decision: {mode}")]

    return {
        "analysis_mode": mode,
        "_skip_full_investigation": skip,
        "activity_log": activity,
    }


# ---------------------------------------------------------------------------
# NODE: Select Diagnostic Tools  ← NEW
# ---------------------------------------------------------------------------

def select_diagnostic_tools_node(state: AgentState, db: Session) -> Dict:
    """
    Decide which tools are actually needed based on the context and mode.
    Avoids running every tool every time (Requirement 12).
    """
    selected_tools = ["symptom_patterns", "appliance_history"]
    
    appliance_ctx = state.get("appliance_context") or {}
    has_error_codes = state.get("_has_error_codes", False)
    mode = state.get("analysis_mode", "fresh_investigation")
    
    if mode == "reinvestigation_required":
        selected_tools.append("repair_outcomes")
    
    if has_error_codes:
        selected_tools.append("manual_lookup")
        
    if appliance_ctx.get("warranty_expiry"):
        selected_tools.append("warranty")
    
    log = (state.get("activity_log") or []) + [f"Selected diagnostic tools: {', '.join(selected_tools).replace('_', ' ')}"]
    
    return {
        "selected_tools": selected_tools,
        "activity_log": log
    }


# ---------------------------------------------------------------------------
# NODE: Analyze Appliance History
# ---------------------------------------------------------------------------

def analyze_history_node(state: AgentState, db: Session) -> Dict:
    """Run appliance_history_tool to get structured history summary."""
    selected = state.get("selected_tools")
    if selected is not None and "appliance_history" not in selected:
        return {}
        
    appliance_id = state["appliance_id"]
    errors = list(state.get("errors") or [])
    history = {}
    try:
        history = get_appliance_history(db, appliance_id)
    except Exception as e:
        errors.append(f"History analysis error: {e}")

    return {"history_analysis": history, "errors": errors}


# ---------------------------------------------------------------------------
# NODE: Analyze Symptoms
# ---------------------------------------------------------------------------

def analyze_symptoms_node(state: AgentState, db: Session) -> Dict:
    """Run symptom_pattern_tool on collected symptoms."""
    selected = state.get("selected_tools")
    if selected is not None and "symptom_patterns" not in selected:
        return {}

    errors = list(state.get("errors") or [])
    analysis = {}
    try:
        analysis = analyze_symptom_patterns(db=db, issue_id=state["issue_id"])
    except Exception as e:
        errors.append(f"Symptom analysis error: {e}")

    log = (state.get("activity_log") or []) + ["Analyzed symptom patterns."]
    return {"symptom_analysis": analysis, "errors": errors, "activity_log": log}


# ---------------------------------------------------------------------------
# NODE: Analyze Warranty
# ---------------------------------------------------------------------------

def analyze_warranty_node(state: AgentState, db: Session) -> Dict:
    """Run warranty_tool."""
    selected = state.get("selected_tools")
    if selected is not None and "warranty" not in selected:
        return {}

    appliance_ctx = state.get("appliance_context") or {}
    errors = list(state.get("errors") or [])
    w_info = {}
    try:
        w_info = check_warranty_status(db=db, appliance_id=state["appliance_id"])
    except Exception as e:
        errors.append(f"Warranty evaluation error: {e}")

    return {"warranty_analysis": w_info, "errors": errors}


# ---------------------------------------------------------------------------
# NODE: Analyze Repairs
# ---------------------------------------------------------------------------

def analyze_repairs_node(state: AgentState, db: Session) -> Dict:
    """Run repair_outcome_tool to review past repair history."""
    selected = state.get("selected_tools")
    if selected is not None and "repair_outcomes" not in selected:
        return {}

    appliance_id = state["appliance_id"]
    errors = list(state.get("errors") or [])
    repair_analysis = {}
    try:
        repair_analysis = analyze_repair_outcomes(db, appliance_id)
    except Exception as e:
        errors.append(f"Repair analysis error: {e}")

    return {"repair_analysis": repair_analysis, "errors": errors}


# ---------------------------------------------------------------------------
# NODE: Manual / Error Code Lookup (CONDITIONAL — only if error codes exist)
# ---------------------------------------------------------------------------

def manual_lookup_node(state: AgentState, db: Session) -> Dict:
    """
    Look up error codes in the local knowledge base.
    Only called when symptom values match known error-code patterns.
    """
    selected = state.get("selected_tools")
    if selected is not None and "manual_lookup" not in selected:
        return {}

    issue_ctx = state.get("issue_context") or {}
    appliance_ctx = state.get("appliance_context") or {}
    symptoms = issue_ctx.get("symptoms", [])
    brand = (appliance_ctx.get("brand") or "").lower()
    category = (appliance_ctx.get("category") or "").lower()

    errors = list(state.get("errors") or [])
    results = []

    for symptom in symptoms:
        code = (symptom.get("value") or "").strip()
        if code:
            try:
                result = lookup_error_code(brand, category, code.lower())
                if result.get("found"):
                    results.append(result)
            except Exception as e:
                errors.append(f"Manual lookup error for code '{code}': {e}")

    log = (state.get("activity_log") or []) + [f"Manual error code lookup checked {len(symptoms)} code(s)."]
    return {
        "manual_lookup": {"results": results, "codes_checked": len(symptoms)},
        "errors": errors,
        "activity_log": log,
    }


# ---------------------------------------------------------------------------
# NODE: Generate Hypotheses (Deterministic)
# ---------------------------------------------------------------------------

def generate_hypotheses_node(state: AgentState, db: Session) -> Dict:
    """
    Build a ranked list of plausible diagnostic hypotheses from tool evidence.
    No LLM involved — purely deterministic scoring.
    If we are in REINVESTIGATION mode, also inject history match as evidence.
    """
    hypotheses = []
    evidence_summary = {}

    history = state.get("history_analysis") or {}
    symptom = state.get("symptom_analysis") or {}
    warranty = state.get("warranty_analysis") or {}
    repair = state.get("repair_analysis") or {}
    lookup = state.get("manual_lookup") or {}
    memories = state.get("memories") or []
    issue_ctx = state.get("issue_context") or {}
    history_match = state.get("history_match") or {}
    mode = state.get("analysis_mode", "fresh_investigation")

    # Evidence: history match (for reinvestigation — use as weak evidence)
    if mode == "reinvestigation_required" and history_match.get("match_found"):
        prev_diagnosis = history_match.get("previous_diagnosis") or ""
        if prev_diagnosis:
            hypotheses.append({
                "hypothesis": f"Previous diagnosis: {prev_diagnosis[:200]}",
                "evidence": f"Prior issue matched at {history_match.get('similarity_score', 0):.0%}; previous repair outcome: {history_match.get('previous_outcome', 'unknown')}.",
                "confidence": "medium",
                "source": "history_match",
            })
        evidence_summary["history_match"] = history_match

    # Evidence: recurring problems
    recurring = history.get("recurring_problems", [])
    if recurring:
        for r in recurring:
            hypotheses.append({
                "hypothesis": f"Recurring issue: {r['pattern']}",
                "evidence": f"Observed {r['occurrence_count']} times.",
                "confidence": "high",
                "source": "history_analysis",
            })
        evidence_summary["recurring_problems"] = recurring

    # Evidence: known symptom patterns
    known_symptoms = symptom.get("known_symptoms_repeated", [])
    if known_symptoms:
        for ks in known_symptoms:
            hypotheses.append({
                "hypothesis": f"Previously seen symptom: {ks['symptom']}",
                "evidence": f"Previously observed {ks['previous_occurrences']} time(s).",
                "confidence": "medium",
                "source": "symptom_pattern",
            })
        evidence_summary["known_symptom_patterns"] = known_symptoms

    # Evidence: unusual symptoms
    unusual = symptom.get("unusual_new_symptoms", [])
    if unusual:
        hypotheses.append({
            "hypothesis": f"New/unusual symptoms detected: {', '.join(unusual)}",
            "evidence": "These symptoms have not been seen on this appliance before.",
            "confidence": "low",
            "source": "symptom_pattern",
        })
        evidence_summary["unusual_symptoms"] = unusual

    # Evidence: failed repairs
    failed_fixes = repair.get("failed_fixes", 0)
    if failed_fixes > 0:
        hypotheses.append({
            "hypothesis": "Previous repair attempts have not resolved the root cause.",
            "evidence": f"{failed_fixes} failed repair(s) on record.",
            "confidence": "medium",
            "source": "repair_analysis",
        })
        evidence_summary["failed_repairs"] = failed_fixes

    # Evidence: error code lookup
    lookup_results = lookup.get("results", [])
    if lookup_results:
        for lr in lookup_results:
            for match in lr.get("matches", []):
                hypotheses.append({
                    "hypothesis": f"Error code indicates: {match.get('possible_meaning', 'Unknown')}",
                    "evidence": f"Code {lr['query'].get('error_code', '?').upper()} — {match.get('possible_meaning')}",
                    "confidence": "high",
                    "source": "manual_lookup",
                })
        evidence_summary["error_code_matches"] = lookup_results

    # Evidence: relevant memories
    if memories:
        for mem in memories[:3]:  # top 3 memories
            hypotheses.append({
                "hypothesis": f"Memory ({mem['type']}): {mem['content'][:120]}",
                "evidence": f"Importance score: {mem['importance']}",
                "confidence": "medium",
                "source": "long_term_memory",
            })
        evidence_summary["memory_insights"] = len(memories)

    # Fallback: if no specific hypothesis was generated, generate working hypothesis from title, description, and symptoms (if present)
    symptoms = issue_ctx.get("symptoms", [])
    if not hypotheses:
        symptom_names = [s.get("name") or s.get("value") for s in symptoms if s.get("name") or s.get("value")] if symptoms else []
        symptom_str = f" exhibiting observed symptoms: {', '.join(filter(None, symptom_names))}" if symptom_names else ""
        title = issue_ctx.get("title") or "reported malfunction"
        desc = issue_ctx.get("description") or ""
        hypotheses.append({
            "hypothesis": f"Investigation into {title}{symptom_str}.",
            "evidence": f"Initial report indicates severity '{issue_ctx.get('severity', 'medium')}'. Details: {desc if desc else title}.",
            "confidence": "medium",
            "source": "problem_description_analysis",
        })

    evidence_summary["warranty_status"] = warranty.get("warranty_status", "unknown")
    evidence_summary["issue_title"] = issue_ctx.get("title", "")
    evidence_summary["issue_description"] = issue_ctx.get("description", "")

    log = (state.get("activity_log") or []) + ["Compared diagnostic hypotheses."]
    return {
        "hypotheses": hypotheses,
        "evidence": evidence_summary,
        "activity_log": log,
    }


# ---------------------------------------------------------------------------
# NODE: Evaluate Evidence (Reflection)
# ---------------------------------------------------------------------------

def evaluate_evidence_node(state: AgentState, db: Session) -> Dict:
    """
    Assess whether there is sufficient evidence for LLM synthesis.
    Symptoms are optional additional evidence; problem title, description, appliance details,
    history, and deterministic tool outputs provide the core diagnostic basis.
    """
    hypotheses = state.get("hypotheses") or []
    issue_ctx = state.get("issue_context") or {}
    title = (issue_ctx.get("title") or "").strip()
    description = (issue_ctx.get("description") or "").strip()

    missing = []
    if not hypotheses:
        missing.append("No diagnostic hypotheses could be formed from available data.")

    # Sufficient when hypotheses exist and there is a problem title or description
    sufficient = len(hypotheses) >= 1 and (bool(title) or bool(description))

    uncertainty = None
    if missing:
        uncertainty = (
            "The following information is needed for a complete diagnosis: "
            + " ".join(missing)
            + " Targeted diagnostic questions: "
            + "(1) Does the appliance display any alphanumeric error codes on its display panel? "
            + "(2) Does the issue occur consistently, or intermittently under specific cycles/temperatures? "
            + "(3) Are there noticeable vibrations, unusual sounds (buzzing, grinding, clicking), or signs of leaks/frost/odors?"
        )
    elif len(hypotheses) == 1:
        uncertainty = "Working diagnostic hypothesis formed based on appliance details and reported issue description."
    elif all(h.get("confidence") == "low" for h in hypotheses):
        uncertainty = "All hypotheses are low-confidence. Additional inspection may be recommended."

    log = (state.get("activity_log") or []) + ["Evaluated evidence."]
    return {
        "_evidence_sufficient": sufficient,
        "uncertainty": uncertainty,
        "activity_log": log,
    }


# ---------------------------------------------------------------------------
# NODE: LLM Synthesis
# ---------------------------------------------------------------------------

SYNTHESIS_SYSTEM_PROMPT = """You are a HomeRepair AI diagnostic assistant.

You receive structured diagnostic evidence from deterministic tools. Your role is to:
1. Interpret the evidence and compare the hypotheses
2. Identify the most likely cause(s)
3. Explain the reasoning in plain language
4. Note any uncertainty or gaps
5. Provide a clear, actionable recommendation

IMPORTANT SAFETY RULES:
- NEVER produce DIY instructions involving:
  * live electrical wiring or internal control board testing under live power
  * high voltage components (capacitors, magnetrons, main transformers)
  * gas supply lines, gas valves, or combustion burners
  * sealed refrigerants, compressor tapping, or refrigerant recovery/recharge
  * dangerous mechanical disassembly involving pressurized springs or heavy internal components
- For any of the above hazards: ALWAYS recommend a qualified professional service in "service_recommendation" — do not provide DIY instructions.
- Only safe, low-risk homeowner checks are permitted (e.g., verifying power cord is plugged in, inspecting filters, checking water shut-off valves, leveling legs, load redistribution).
- Do NOT calculate costs, frequencies, dates, or statistics — these are already provided.
- Do NOT invent appliance data, repair history, error codes, symptoms, or warranties.
- All factual information must come from the evidence provided to you.
- Keep the recommendation practical, clear, and safe for a homeowner audience.

OUTPUT FORMAT:
You MUST respond with valid JSON matching exactly this structure:
{
  "summary": "Brief 1-2 sentence problem summary",
  "likely_causes": [
    {
      "cause": "Name of the cause",
      "reason": "Why this is likely",
      "confidence": "high|medium|low"
    }
  ],
  "evidence": [
    {
      "observation": "What was observed",
      "supports": "What this evidence supports"
    }
  ],
  "recommended_next_step": "Actionable next step",
  "service_recommendation": "Professional service advice (if applicable) or N/A",
  "warranty_recommendation": "Warranty advice (if applicable) or N/A"
}
"""

def llm_synthesis_node(state: AgentState, db: Session) -> Dict:
    """
    Use the OpenRouter LLM to synthesize evidence into a recommendation.
    The LLM receives only structured evidence — it does NOT have access to
    raw database queries or internal state.
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    errors = list(state.get("errors") or [])
    recommendation = None
    print("\n[DEBUG-AGENT] 1. Entered llm_synthesis_node")

    try:
        import httpx
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        import json
        import re
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        load_dotenv(dotenv_path=env_path, override=True)

        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        model = os.getenv("OPENROUTER_MODEL")

        print(f"\n[DEBUG-AGENT] 2. Loaded OPENROUTER_MODEL from env: {model}")
        print(f"[DEBUG-AGENT] 3. Target URL will be: {base_url}/chat/completions")
        logger.info(f"--- [DEBUG] loaded model name: {model}")
        logger.info(f"--- [DEBUG] request URL: {base_url}/chat/completions")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")
        if not model:
            raise ValueError("OPENROUTER_MODEL is not set.")

        issue_ctx = state.get("issue_context") or {}
        appliance_ctx = state.get("appliance_context") or {}
        hypotheses = state.get("hypotheses") or []
        evidence = state.get("evidence") or {}
        warranty = state.get("warranty_analysis") or {}
        memories = state.get("memories") or []
        history_match = state.get("history_match") or {}
        mode = state.get("analysis_mode", "fresh_investigation")

        # Include history context in evidence if reinvestigation
        history_context = ""
        if mode == "reinvestigation_required" and history_match.get("match_found"):
            history_context = f"""
PREVIOUS SIMILAR ISSUE:
  Similarity: {history_match.get('similarity_score', 0):.0%}
  Prior Diagnosis: {history_match.get('previous_diagnosis', 'N/A')}
  Prior Outcome: {history_match.get('previous_outcome', 'N/A')}
  Reason for Reinvestigation: {history_match.get('similarity_reason', 'N/A')}
"""

        evidence_text = f"""
APPLIANCE: {appliance_ctx.get('brand', 'Unknown')} {appliance_ctx.get('model_number', '')} ({appliance_ctx.get('category', '')})
LOCATION: {appliance_ctx.get('location', 'Unknown')}

ISSUE REPORTED: {issue_ctx.get('title', '')}
DESCRIPTION: {issue_ctx.get('description', 'No description provided.')}
SEVERITY: {issue_ctx.get('severity', 'unknown')}
INVESTIGATION MODE: {mode.replace('_', ' ').upper()}

RECORDED SYMPTOMS: {', '.join(
    f"{s['name']}: {s['value']}" + (f" {s['unit']}" if s.get('unit') else '')
    for s in issue_ctx.get('symptoms', [])
) or 'None recorded'}

WARRANTY STATUS: {warranty.get('warranty_status', 'unknown')}
DAYS REMAINING: {warranty.get('days_remaining', 'N/A')}
{history_context}
DIAGNOSTIC HYPOTHESES:
{chr(10).join(
    f"  [{i+1}] {h['hypothesis']} (confidence: {h['confidence']}) — {h['evidence']}"
    for i, h in enumerate(hypotheses)
) or '  No hypotheses available.'}

RECURRING PROBLEMS: {', '.join(r['pattern'] for r in evidence.get('recurring_problems', [])) or 'None detected'}
UNUSUAL NEW SYMPTOMS: {', '.join(evidence.get('unusual_symptoms', [])) or 'None'}
FAILED REPAIRS ON RECORD: {evidence.get('failed_repairs', 0)}

RELEVANT APPLIANCE MEMORIES:
{chr(10).join(f"  - [{m['type']}] {m['content'][:200]}" for m in memories[:5]) or '  No prior memories.'}
"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://homerepair-ai.local",
            "X-Title": "HomeRepair AI",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"Based on this evidence, provide a diagnostic recommendation in JSON format:\n\n{evidence_text}"}
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
        }

        print("\n[DEBUG-AGENT] 4. Sending payload to OpenRouter...")
        logger.info("--- [DEBUG] Sending HTTP POST to OpenRouter ---")
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            print(f"[DEBUG-AGENT] 5. Received HTTP status code: {response.status_code}")
            logger.info(f"--- [DEBUG] HTTP status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[DEBUG-AGENT] 6. ERROR response text: {response.text}")
                logger.error(f"--- [DEBUG] OpenRouter error response: {response.text}")
                response.raise_for_status()

            response_json = response.json()
            content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            content = content.strip() if content else ""
            logger.info("--- [DEBUG] OpenRouter success response parsed.")
        except Exception as e:
            logger.error(f"--- [DEBUG] HTTP request failed: {e}")
            raise

        # Extract JSON block using regex if wrapped in markdown
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL | re.IGNORECASE)
        if json_match:
            content = json_match.group(1)
        else:
            # If no code block, try to find the outermost curly braces
            brace_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if brace_match:
                content = brace_match.group(1)

        parsed_response = json.loads(content.strip())
        recommendation = parsed_response
        print(f"[DEBUG-AGENT] 7. Successfully parsed JSON from OpenRouter.")

    except json.JSONDecodeError as e:
        print(f"[DEBUG-AGENT] 8. JSON Decode Error: {e}")
        errors.append(f"Failed to parse LLM JSON: {e}")
        recommendation = {"error": f"LLM returned invalid JSON structure: {str(e)}\nRaw output: {content}"}
    except ValueError as e:
        print(f"[DEBUG-AGENT] 8. Value Error (likely config): {e}")
        errors.append(f"LLM configuration error: {e}")
        recommendation = {"error": f"LLM synthesis unavailable: {str(e)}. Please check OPENROUTER_API_KEY and OPENROUTER_MODEL in your .env file."}
    except Exception as e:
        print(f"[DEBUG-AGENT] 8. Exception in LLM HTTP call: {e}")
        errors.append(f"LLM synthesis error: {e}")
        recommendation = {"error": f"OpenRouter API error: {str(e)}"}

    log = (state.get("activity_log") or []) + ["Prepared recommendation."]
    return {
        "recommendation": recommendation,
        "_should_store_memory": bool(recommendation and isinstance(recommendation, dict) and "error" not in recommendation),
        "activity_log": log,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# NODE: Historical Match Finalize (skip full investigation)  ← NEW
# ---------------------------------------------------------------------------

def historical_match_finalize_node(state: AgentState, db: Session) -> Dict:
    """
    For HISTORICAL_MATCH mode: build a response from previous knowledge
    without running a full LLM investigation.
    """
    history_match = state.get("history_match") or {}
    issue_ctx = state.get("issue_context") or {}
    appliance_ctx = state.get("appliance_context") or {}
    memories = state.get("memories") or []
    warranty = state.get("warranty_analysis") or {}

    prev_diagnosis = history_match.get("previous_diagnosis") or ""
    prev_outcome = history_match.get("previous_outcome") or "unknown"
    prev_repair = history_match.get("previous_repair") or "Not recorded"
    similarity = history_match.get("similarity_score", 0)
    confidence = history_match.get("confidence", "medium")

    summary = (
        f"A substantially similar issue was previously diagnosed on this appliance "
        f"(similarity: {similarity:.0%}). Previous repair outcome: {prev_outcome}."
    )
    if prev_diagnosis:
        summary = f"{prev_diagnosis} (Reused from history — {similarity:.0%} match, outcome: {prev_outcome}.)"

    likely_causes = []
    if prev_diagnosis:
        likely_causes = [{
            "cause": "Recurrence of previously diagnosed problem",
            "reason": f"Prior diagnosis: {prev_diagnosis[:200]}",
            "confidence": confidence,
        }]

    evidence_items = [
        {
            "observation": f"Historical similarity score: {similarity:.0%}",
            "supports": "Strong match to previous incident on same appliance",
        },
        {
            "observation": f"Previous repair outcome: {prev_outcome}",
            "supports": "Confirms previous resolution was successful",
        },
    ]
    if memories:
        evidence_items.append({
            "observation": f"{len(memories)} relevant appliance memories retrieved",
            "supports": "Consistent with established pattern for this appliance",
        })

    warranty_rec = "N/A"
    if warranty.get("warranty_status") in ("active", "expiring_soon"):
        warranty_rec = (
            f"Appliance warranty is {warranty.get('warranty_status')}. "
            "Consider filing a warranty claim for professional inspection."
        )

    activity = (state.get("activity_log") or []) + [
        "Applied previous successful diagnosis.",
        "Skipped redundant investigation — historical knowledge sufficient.",
    ]

    final = {
        "issue_id": str(state.get("issue_id")),
        "analysis_status": "completed",
        "analysis_mode": "historical_match",
        "summary": summary,
        "likely_causes": likely_causes,
        "evidence": evidence_items,
        "uncertainty": "Previous repair was successful. Monitor if symptoms recur or worsen.",
        "recommended_next_step": prev_repair if prev_repair != "Not recorded" else "Apply the same repair that resolved the previous similar issue.",
        "service_recommendation": "N/A",
        "warranty_recommendation": warranty_rec,
        "repair_history": [],
        "activity_log": activity,
        "errors": [e for e in (state.get("errors") or []) if e],
    }

    return {"final_result": final}


# ---------------------------------------------------------------------------
# NODE: Insufficient Data Finalize  ← NEW
# ---------------------------------------------------------------------------

def insufficient_data_finalize_node(state: AgentState, db: Session) -> Dict:
    """
    For INSUFFICIENT_DATA mode: return targeted questions without attempting diagnosis.
    """
    issue_ctx = state.get("issue_context") or {}
    activity = (state.get("activity_log") or []) + [
        "Determined that additional information is required before diagnosis.",
    ]

    final = {
        "issue_id": str(state.get("issue_id")),
        "analysis_status": "insufficient_data",
        "analysis_mode": "insufficient_data",
        "summary": "Insufficient information to establish a reliable diagnosis.",
        "likely_causes": [],
        "evidence": [],
        "uncertainty": (
            "The issue description is too vague for a reliable diagnosis. "
            "Targeted questions: "
            "(1) What exactly is happening — is the appliance making noise, not turning on, leaking, heating incorrectly, or displaying an error code? "
            "(2) When did this start, and does it happen every time or intermittently? "
            "(3) Are there any error codes, flashing lights, or unusual sounds? "
            "(4) Has anything changed recently — new setting, power outage, or use pattern change?"
        ),
        "recommended_next_step": (
            "Please provide a more detailed problem description and then re-run the diagnosis."
        ),
        "service_recommendation": "N/A",
        "warranty_recommendation": "N/A",
        "repair_history": [],
        "activity_log": activity,
        "errors": [],
    }

    return {"final_result": final}


# ---------------------------------------------------------------------------
# NODE: Store Memory
# ---------------------------------------------------------------------------

def store_memory_node(state: AgentState, db: Session) -> Dict:
    """
    Persist only meaningful, non-duplicate insights as long-term appliance memories.
    Stores: recurring faults, successful fix patterns, failed repair patterns.
    Does NOT store: raw analysis, temporary statistics, generic advice.
    """
    appliance_id = state["appliance_id"]
    errors = list(state.get("errors") or [])
    memories_stored = 0

    try:
        hypotheses = state.get("hypotheses") or []
        evidence = state.get("evidence") or {}
        recommendation = state.get("recommendation") or {}

        # Store high-confidence recurring fault memories
        for h in hypotheses:
            if h.get("confidence") == "high" and h.get("source") in (
                "history_analysis", "manual_lookup"
            ):
                content = h["hypothesis"]
                store_memory(
                    db=db,
                    appliance_id=appliance_id,
                    memory_type=MemoryType.RECURRING_FAULT,
                    content=content,
                    importance_score=7.0,
                )
                memories_stored += 1

        # Store failed repair pattern memory if relevant
        failed = evidence.get("failed_repairs", 0)
        if failed and failed >= 2:
            content = f"Appliance has {failed} failed repair attempts on record. Consider alternative repair approach."
            store_memory(
                db=db,
                appliance_id=appliance_id,
                memory_type=MemoryType.FAILED_FIX,
                content=content,
                importance_score=6.0,
            )
            memories_stored += 1

        # Store successful diagnosis as a memory if LLM produced a result
        if isinstance(recommendation, dict) and "summary" in recommendation:
            summary = recommendation.get("summary", "")
            if summary and len(summary) > 20:
                content = f"Diagnosis completed: {summary[:300]}"
                store_memory(
                    db=db,
                    appliance_id=appliance_id,
                    memory_type=MemoryType.PREVIOUS_REPAIR,
                    content=content,
                    importance_score=5.0,
                )
                memories_stored += 1

    except Exception as e:
        errors.append(f"Memory storage error: {e}")

    log = (state.get("activity_log") or []) + [
        f"Stored {memories_stored} new memory item(s)." if memories_stored else "No new memories to store."
    ]
    return {"activity_log": log, "errors": errors}


# ---------------------------------------------------------------------------
# NODE: Finalize Result
# ---------------------------------------------------------------------------

def finalize_result_node(state: AgentState, db: Session) -> Dict:
    """
    Assemble the final safe response matching the requested structured schema.
    """
    existing_final = state.get("final_result")
    if existing_final and ("error" in existing_final or "analysis_mode" in existing_final):
        return {"final_result": existing_final}

    rec = state.get("recommendation")
    has_error = isinstance(rec, dict) and "error" in rec
    if has_error:
        parsed_rec = {}
        error_msg = rec["error"]
    else:
        parsed_rec = rec if isinstance(rec, dict) else {}
        error_msg = None

    insufficient = not state.get("_evidence_sufficient", False)
    mode = state.get("analysis_mode", "fresh_investigation")
    analysis_status = "insufficient_data" if insufficient else "completed"
    if has_error:
        analysis_status = "error"

    default_summary = (
        "Diagnostic paused: Insufficient problem details recorded to establish a conclusive root cause."
        if insufficient else
        error_msg if error_msg else "Analysis incomplete due to insufficient data or error."
    )
    default_next_step = (
        "Please review the targeted questions in 'What Is Still Uncertain' and provide more problem details before re-running."
        if insufficient else
        "Provide more problem details."
    )

    repair = state.get("repair_analysis") or {}
    repair_history_summary = repair.get("repair_types_attempted", [])

    final = {
        "issue_id": str(state.get("issue_id")),
        "analysis_status": analysis_status,
        "analysis_mode": mode,
        "summary": parsed_rec.get("summary") or default_summary,
        "likely_causes": parsed_rec.get("likely_causes") or [],
        "evidence": parsed_rec.get("evidence") or [],
        "uncertainty": state.get("uncertainty") or "No critical uncertainties identified.",
        "recommended_next_step": parsed_rec.get("recommended_next_step") or default_next_step,
        "service_recommendation": parsed_rec.get("service_recommendation") or "N/A",
        "warranty_recommendation": parsed_rec.get("warranty_recommendation") or "N/A",
        "repair_history": repair_history_summary,
        "activity_log": state.get("activity_log") or [],
        "errors": [e for e in (state.get("errors") or []) if e],
    }

    return {"final_result": final}
