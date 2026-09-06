from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.appliance import ApplianceCreate, ApplianceUpdate, ApplianceResponse
from app.schemas.issue import IssueCreate, IssueResponse
from app.schemas.repair import RepairHistoryCreate, RepairHistoryResponse
from app.schemas.symptom import SymptomCreate
from app.services.appliance_service import ApplianceService
from app.services.issue_service import IssueService
from app.services.repair_service import RepairService
from app.models.enums import IssueSeverity

router = APIRouter(prefix="/appliances", tags=["Appliances"])


class ApplianceWithIssueCreate(BaseModel):
    """Create appliance with initial issue in one atomic transaction."""
    # Appliance fields
    name: str = Field(..., min_length=1, description="Name or nickname for the appliance")
    brand: Optional[str] = Field(None)
    model_number: Optional[str] = Field(None)
    category: str = Field(..., description="Appliance category")
    purchase_date: Optional[str] = Field(None)
    warranty_expiry: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)

    # Initial issue fields
    has_issue: Optional[bool] = Field(default=True, description="Whether an initial issue is being logged")
    issue_title: Optional[str] = Field(None, description="Title of the initial problem")
    issue_description: Optional[str] = Field(None, description="Description of the initial problem")
    issue_severity: Optional[str] = Field(default="medium", description="Severity of the initial problem")
    issue_symptom: Optional[str] = Field(None, description="Observed symptom description (optional)")


@router.post(
    "",
    response_model=ApplianceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create appliance",
    description="Register a new household appliance in the system."
)
def create_appliance(
    appliance_in: ApplianceCreate,
    db: Session = Depends(get_db)
):
    return ApplianceService.create_appliance(db, appliance_in)


@router.post(
    "/with-issue",
    response_model=ApplianceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create appliance with initial issue",
    description="Atomically create an appliance and associated initial problem report."
)
def create_appliance_with_issue(
    payload: ApplianceWithIssueCreate,
    db: Session = Depends(get_db)
):
    from app.models.enums import ApplianceCategory
    from datetime import date

    # Check if an initial issue is being logged
    is_logging_issue = (
        payload.has_issue is not False and
        (
            bool(payload.issue_title and payload.issue_title.strip()) or
            bool(payload.issue_description and payload.issue_description.strip()) or
            bool(payload.issue_symptom and payload.issue_symptom.strip()) or
            payload.has_issue is True
        )
    )

    severity = IssueSeverity.MEDIUM
    if is_logging_issue:
        # Enforce required issue fields: Title, Description, and Severity
        if not payload.issue_title or not payload.issue_title.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Problem Title (issue_title) is required and cannot be empty"
            )
        if not payload.issue_description or not payload.issue_description.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Problem Description (issue_description) is required and cannot be empty"
            )
        
        severity_str = (payload.issue_severity or "medium").lower().strip()
        severity_map = {
            "low": IssueSeverity.LOW,
            "medium": IssueSeverity.MEDIUM,
            "high": IssueSeverity.HIGH,
            "critical": IssueSeverity.CRITICAL,
        }
        if severity_str not in severity_map:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"issue_severity must be one of: {list(severity_map.keys())}"
            )
        severity = severity_map[severity_str]

    # Build ApplianceCreate
    purchase_date = None
    warranty_expiry = None
    if payload.purchase_date:
        try:
            purchase_date = date.fromisoformat(payload.purchase_date)
        except ValueError:
            pass
    if payload.warranty_expiry:
        try:
            warranty_expiry = date.fromisoformat(payload.warranty_expiry)
        except ValueError:
            pass

    try:
        category = ApplianceCategory(payload.category) if payload.category else ApplianceCategory.OTHER
    except ValueError:
        category = ApplianceCategory.OTHER
    appliance_in = ApplianceCreate(
        name=payload.name,
        brand=payload.brand,
        model_number=payload.model_number,
        category=category,
        purchase_date=purchase_date,
        warranty_expiry=warranty_expiry,
        location=payload.location,
        notes=payload.notes,
    )
    appliance = ApplianceService.create_appliance(db, appliance_in)

    # Create linked issue if issue was entered
    if is_logging_issue:
        symptoms = []
        if payload.issue_symptom and payload.issue_symptom.strip():
            symptoms = [SymptomCreate(name="Observed Symptom", value=payload.issue_symptom.strip())]
        issue_in = IssueCreate(
            title=payload.issue_title.strip(),
            description=payload.issue_description.strip(),
            severity=severity,
            symptoms=symptoms if symptoms else None,
        )
        IssueService.create_issue(db, appliance.id, issue_in)
        # Refresh to include the new issue in response
        db.refresh(appliance)

    return appliance


@router.get(
    "",
    response_model=List[ApplianceResponse],
    summary="Return active appliances",
    description="Retrieve all currently active registered appliances."
)
def get_active_appliances(
    db: Session = Depends(get_db)
):
    return ApplianceService.get_active_appliances(db)


@router.get(
    "/{appliance_id}",
    response_model=ApplianceResponse,
    summary="Return one appliance",
    description="Retrieve an individual appliance by its unique ID."
)
def get_appliance(
    appliance_id: int,
    db: Session = Depends(get_db)
):
    return ApplianceService.get_appliance_by_id(db, appliance_id)


@router.put(
    "/{appliance_id}",
    response_model=ApplianceResponse,
    summary="Update appliance",
    description="Update appliance metadata, warranty, or location."
)
def update_appliance(
    appliance_id: int,
    appliance_in: ApplianceUpdate,
    db: Session = Depends(get_db)
):
    return ApplianceService.update_appliance(db, appliance_id, appliance_in)


@router.delete(
    "/{appliance_id}",
    response_model=ApplianceResponse,
    summary="Soft deactivate appliance",
    description="Deactivate an appliance without permanently deleting its history."
)
def soft_deactivate_appliance(
    appliance_id: int,
    db: Session = Depends(get_db)
):
    return ApplianceService.soft_delete_appliance(db, appliance_id)


# Nested Issue Endpoints for Appliance
@router.post(
    "/{appliance_id}/issues",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create repair issue",
    description="Report a new problem or breakdown for a specific appliance."
)
def create_appliance_issue(
    appliance_id: int,
    issue_in: IssueCreate,
    db: Session = Depends(get_db)
):
    return IssueService.create_issue(db, appliance_id, issue_in)


@router.get(
    "/{appliance_id}/issues",
    response_model=List[IssueResponse],
    summary="List issues for appliance",
    description="Retrieve all reported issues for a specific appliance."
)
def list_appliance_issues(
    appliance_id: int,
    db: Session = Depends(get_db)
):
    return IssueService.get_appliance_issues(db, appliance_id)


@router.delete(
    "/{appliance_id}/issues/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete issue for appliance",
    description="Delete a specific issue and all its associated symptoms."
)
def delete_appliance_issue(
    appliance_id: int,
    issue_id: int,
    db: Session = Depends(get_db)
):
    issue = IssueService.get_issue_by_id(db, issue_id)
    if issue.appliance_id != appliance_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} does not belong to appliance {appliance_id}"
        )
    IssueService.delete_issue(db, issue_id)
    return None


# Nested Repair History Endpoints for Appliance
@router.get(
    "/{appliance_id}/repairs",
    response_model=List[RepairHistoryResponse],
    summary="Return repair history",
    description="Retrieve the complete repair history log for an appliance."
)
def get_appliance_repairs(
    appliance_id: int,
    db: Session = Depends(get_db)
):
    return RepairService.get_appliance_repairs(db, appliance_id)


@router.post(
    "/{appliance_id}/repairs",
    response_model=RepairHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add completed repair record",
    description="Record a completed maintenance or repair event for an appliance."
)
def add_appliance_repair(
    appliance_id: int,
    repair_in: RepairHistoryCreate,
    db: Session = Depends(get_db)
):
    return RepairService.add_repair_record(db, appliance_id, repair_in)
