from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.appliance import ApplianceCreate, ApplianceUpdate, ApplianceResponse
from app.schemas.issue import IssueCreate, IssueResponse
from app.schemas.repair import RepairHistoryCreate, RepairHistoryResponse
from app.services.appliance_service import ApplianceService
from app.services.issue_service import IssueService
from app.services.repair_service import RepairService

router = APIRouter(prefix="/appliances", tags=["Appliances"])


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
