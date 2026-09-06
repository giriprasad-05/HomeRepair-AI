"""
Agent API endpoint for HomeRepair AI diagnostic agent.

POST /api/agent/investigate/{issue_id}
  Triggers LangGraph investigation. Returns structured result with analysis_mode.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.agent.graph import run_agent

router = APIRouter(prefix="/agent", tags=["Diagnostic Agent"])


class CauseItem(BaseModel):
    cause: str
    reason: str
    confidence: str

class EvidenceItem(BaseModel):
    observation: str
    supports: str

class InvestigateResponse(BaseModel):
    issue_id: str
    analysis_status: str
    analysis_mode: str = "fresh_investigation"
    summary: str = ""
    likely_causes: list[CauseItem] = []
    evidence: list[EvidenceItem] = []
    uncertainty: str = "No critical uncertainties identified."
    recommended_next_step: str = ""
    service_recommendation: str = "N/A"
    warranty_recommendation: str = "N/A"
    repair_history: list[str] = []
    activity_log: list[str] = []
    errors: list[str] = []


@router.post(
    "/investigate/{issue_id}",
    response_model=InvestigateResponse,
    summary="Run AI diagnostic on a repair issue",
    description=(
        "Triggers the LangGraph diagnostic agent for the specified issue. "
        "The agent first checks history (HISTORICAL_MATCH / REINVESTIGATION / FRESH / INSUFFICIENT_DATA), "
        "then selects and runs deterministic tools, and synthesizes a recommendation "
        "using an LLM when evidence is sufficient."
    ),
)
def investigate_issue(
    issue_id: int,
    db: Session = Depends(get_db),
):
    try:
        result = run_agent(issue_id=issue_id, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        )

    if result.get("error") and not result.get("summary"):
        error_msg = result["error"]
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Normalize evidence: can be list[dict] or dict from old paths
    evidence = result.get("evidence", [])
    if isinstance(evidence, dict):
        # Convert from old dict format to list format
        evidence = []

    result["evidence"] = evidence

    # Persist diagnosis directly on the issue record so future history matching has it
    try:
        from app.models.issue import IssueReport
        from app.models.enums import IssueStatus
        import json as _json
        issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
        if issue and result.get("summary"):
            issue.diagnosis_result = _json.dumps({
                "summary": result.get("summary"),
                "likely_causes": result.get("likely_causes", []),
                "evidence": evidence,
                "recommended_next_step": result.get("recommended_next_step"),
                "service_recommendation": result.get("service_recommendation"),
                "warranty_recommendation": result.get("warranty_recommendation"),
                "uncertainty": result.get("uncertainty"),
                "analysis_mode": result.get("analysis_mode"),
            })
            if issue.status == IssueStatus.OPEN:
                issue.status = IssueStatus.REPAIR_RECOMMENDED
            db.commit()
    except Exception as persist_err:
        pass

    return InvestigateResponse(**result)
