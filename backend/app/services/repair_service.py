from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.repair import RepairHistory
from app.schemas.repair import RepairHistoryCreate
from app.services.appliance_service import ApplianceService
from app.services.issue_service import IssueService


class RepairService:
    @staticmethod
    def get_appliance_repairs(db: Session, appliance_id: int) -> List[RepairHistory]:
        # Validate appliance exists
        ApplianceService.get_appliance_by_id(db, appliance_id)
        return db.query(RepairHistory).filter(
            RepairHistory.appliance_id == appliance_id
        ).order_by(RepairHistory.repair_date.desc(), RepairHistory.id.desc()).all()

    @staticmethod
    def add_repair_record(db: Session, appliance_id: int, repair_in: RepairHistoryCreate) -> RepairHistory:
        # Validate appliance exists
        ApplianceService.get_appliance_by_id(db, appliance_id)

        # Validate service cost cannot be negative
        if repair_in.service_cost is not None and repair_in.service_cost < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service cost cannot be negative"
            )

        # Validate issue belongs to appliance if issue_id is provided
        if repair_in.issue_id is not None:
            issue = IssueService.get_issue_by_id(db, repair_in.issue_id)
            if issue.appliance_id != appliance_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Issue {repair_in.issue_id} belongs to appliance {issue.appliance_id}, not appliance {appliance_id}"
                )

        repair = RepairHistory(
            appliance_id=appliance_id,
            issue_id=repair_in.issue_id,
            repair_type=repair_in.repair_type,
            description=repair_in.description,
            parts_replaced=repair_in.parts_replaced,
            service_cost=repair_in.service_cost,
            repair_date=repair_in.repair_date,
            outcome=repair_in.outcome,
            notes=repair_in.notes,
        )
        db.add(repair)
        db.commit()
        db.refresh(repair)
        return repair
