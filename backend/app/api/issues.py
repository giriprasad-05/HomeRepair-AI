from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.issue import IssueUpdate, IssueResponse
from app.schemas.symptom import SymptomCreate, SymptomResponse
from app.services.issue_service import IssueService
from app.services.symptom_service import SymptomService

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
