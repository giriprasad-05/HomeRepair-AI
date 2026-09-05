from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.issue import IssueReport
from app.models.symptom import Symptom
from app.models.enums import IssueStatus
from app.schemas.issue import IssueCreate, IssueUpdate
from app.services.appliance_service import ApplianceService


class IssueService:
    @staticmethod
    def get_issue_by_id(db: Session, issue_id: int) -> IssueReport:
        issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with id {issue_id} not found"
            )
        return issue

    @staticmethod
    def get_appliance_issues(db: Session, appliance_id: int) -> List[IssueReport]:
        # Validate appliance exists
        ApplianceService.get_appliance_by_id(db, appliance_id)
        return db.query(IssueReport).filter(
            IssueReport.appliance_id == appliance_id
        ).order_by(IssueReport.reported_at.desc()).all()

    @staticmethod
    def create_issue(db: Session, appliance_id: int, issue_in: IssueCreate) -> IssueReport:
        # Validate appliance exists
        ApplianceService.get_appliance_by_id(db, appliance_id)

        issue = IssueReport(
            appliance_id=appliance_id,
            title=issue_in.title,
            description=issue_in.description,
            severity=issue_in.severity,
            status=issue_in.status,
        )
        db.add(issue)
        db.flush()

        # Add initial symptoms if provided
        if issue_in.symptoms:
            for s_in in issue_in.symptoms:
                symptom = Symptom(
                    issue_id=issue.id,
                    name=s_in.name,
                    value=s_in.value,
                    unit=s_in.unit
                )
                db.add(symptom)

        db.commit()
        db.refresh(issue)
        return issue

    @staticmethod
    def update_issue(db: Session, issue_id: int, issue_in: IssueUpdate) -> IssueReport:
        issue = IssueService.get_issue_by_id(db, issue_id)

        update_data = issue_in.model_dump(exclude_unset=True)

        # Handle automatic resolution timestamp if marking as resolved
        if update_data.get("status") == IssueStatus.RESOLVED and "resolved_at" not in update_data:
            update_data["resolved_at"] = datetime.now(timezone.utc)
        elif update_data.get("status") and update_data.get("status") != IssueStatus.RESOLVED:
            # If reopened/moving away from resolved, clear resolved_at unless explicitly specified
            if "resolved_at" not in update_data:
                update_data["resolved_at"] = None

        for field, value in update_data.items():
            setattr(issue, field, value)

        db.commit()
        db.refresh(issue)
        return issue
