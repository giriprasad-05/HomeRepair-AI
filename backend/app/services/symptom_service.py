from typing import List
from sqlalchemy.orm import Session

from app.models.symptom import Symptom
from app.schemas.symptom import SymptomCreate
from app.services.issue_service import IssueService


class SymptomService:
    @staticmethod
    def get_issue_symptoms(db: Session, issue_id: int) -> List[Symptom]:
        # Validate issue exists
        IssueService.get_issue_by_id(db, issue_id)
        return db.query(Symptom).filter(
            Symptom.issue_id == issue_id
        ).order_by(Symptom.recorded_at.asc()).all()

    @staticmethod
    def add_symptom(db: Session, issue_id: int, symptom_in: SymptomCreate) -> Symptom:
        # Validate issue exists
        IssueService.get_issue_by_id(db, issue_id)

        symptom = Symptom(
            issue_id=issue_id,
            name=symptom_in.name,
            value=symptom_in.value,
            unit=symptom_in.unit
        )
        db.add(symptom)
        db.commit()
        db.refresh(symptom)
        return symptom
