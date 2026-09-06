from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.issue import IssueUpdate, IssueResponse, IssueOutcomeUpdate
from app.schemas.symptom import SymptomCreate, SymptomResponse
from app.services.issue_service import IssueService
from app.services.symptom_service import SymptomService
from app.models.enums import IssueStatus, MemoryType
from app.services.memory_service import store_memory

router = APIRouter(prefix="/issues", tags=["Issues & Symptoms"])


@router.get(
    "/{issue_id}",
    response_model=IssueResponse,
    summary="Get individual issue",
    description="Retrieve full details for a reported issue, including its symptoms."
)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):
    return IssueService.get_issue_by_id(db, issue_id)


@router.put(
    "/{issue_id}",
    response_model=IssueResponse,
    summary="Update issue status/details",
    description="Update issue diagnosis progress, status (e.g. resolved), or severity."
)
def update_issue(
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(get_db)
):
    return IssueService.update_issue(db, issue_id, issue_in)


@router.delete(
    "/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete issue",
    description="Permanently delete an issue and all its associated symptoms."
)
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):
    IssueService.delete_issue(db, issue_id)
    return None


@router.patch(
    "/{issue_id}/diagnosis",
    response_model=IssueResponse,
    summary="Store AI diagnosis result on issue",
    description="Persist the AI investigation result against this issue for future history matching."
)
def store_diagnosis(
    issue_id: int,
    diagnosis_json: str,
    db: Session = Depends(get_db)
):
    """Store the diagnosis_result JSON on the issue record."""
    issue = IssueService.get_issue_by_id(db, issue_id)
    issue.diagnosis_result = diagnosis_json
    issue.status = IssueStatus.REPAIR_RECOMMENDED
    db.commit()
    db.refresh(issue)
    return issue


@router.patch(
    "/{issue_id}/outcome",
    response_model=IssueResponse,
    summary="Record repair outcome",
    description="Record whether a repair was successful, failed, or partially resolved. This outcome affects future AI decisions."
)
def record_outcome(
    issue_id: int,
    outcome_in: IssueOutcomeUpdate,
    db: Session = Depends(get_db)
):
    """
    Store repair outcome. This is the critical feedback loop that makes
    the agent learn from past repairs.
    """
    issue = IssueService.get_issue_by_id(db, issue_id)

    issue.repair_outcome = outcome_in.repair_outcome
    issue.repair_notes = outcome_in.repair_notes

    # Update status based on outcome
    if outcome_in.status:
        issue.status = outcome_in.status
    elif outcome_in.repair_outcome.value == "successful":
        issue.status = IssueStatus.RESOLVED
        issue.resolved_at = datetime.now(timezone.utc)
    elif outcome_in.repair_outcome.value == "failed":
        issue.status = IssueStatus.FAILED

    db.commit()
    db.refresh(issue)

    # Store meaningful memory based on outcome
    outcome_val = outcome_in.repair_outcome.value
    if outcome_val == "successful" and outcome_in.repair_notes:
        store_memory(
            db=db,
            appliance_id=issue.appliance_id,
            memory_type=MemoryType.SUCCESSFUL_FIX,
            content=f"Successful repair: {outcome_in.repair_notes[:300]}",
            importance_score=8.0,
        )
    elif outcome_val == "failed" and outcome_in.repair_notes:
        store_memory(
            db=db,
            appliance_id=issue.appliance_id,
            memory_type=MemoryType.FAILED_FIX,
            content=f"Failed repair attempt: {outcome_in.repair_notes[:300]}",
            importance_score=7.0,
        )
    elif outcome_val == "partially_resolved":
        notes = outcome_in.repair_notes or "No notes provided."
        store_memory(
            db=db,
            appliance_id=issue.appliance_id,
            memory_type=MemoryType.APPLIANCE_BEHAVIOR,
            content=f"Partially resolved issue: {notes[:300]}",
            importance_score=6.0,
        )

    return issue


@router.post(
    "/{issue_id}/symptoms",
    response_model=SymptomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add symptom",
    description="Record an observed symptom (e.g., error code, noise, temperature) for an issue."
)
def add_symptom(
    issue_id: int,
    symptom_in: SymptomCreate,
    db: Session = Depends(get_db)
):
    return SymptomService.add_symptom(db, issue_id, symptom_in)


@router.get(
    "/{issue_id}/symptoms",
    response_model=List[SymptomResponse],
    summary="Get issue symptoms",
    description="List all recorded symptoms for a specific issue."
)
def get_issue_symptoms(
    issue_id: int,
    db: Session = Depends(get_db)
):
    return SymptomService.get_issue_symptoms(db, issue_id)
