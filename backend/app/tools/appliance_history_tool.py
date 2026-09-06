from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.appliance_service import ApplianceService
from app.services.issue_service import IssueService
from app.services.repair_service import RepairService
from app.services.repair_analytics import (
    calculate_appliance_metrics,
    detect_recurring_problems
)

def get_appliance_history(db: Session, appliance_id: int) -> Dict[str, Any]:
    """
    Fetches an appliance's complete history including issues, repairs,
    and computed deterministic analytics.
    """
    appliance = ApplianceService.get_appliance_by_id(db, appliance_id)
    if not appliance:
        return {"error": f"Appliance with id {appliance_id} not found."}
        
    issues = IssueService.get_appliance_issues(db, appliance_id)
    repairs = RepairService.get_appliance_repairs(db, appliance_id)
    
    # Extract the database models from the Pydantic responses if needed
    # Wait, the services return Pydantic schemas. The analytics functions expect SQLAlchemy models.
    # Let's adjust the tool to fetch SQLAlchemy models directly, or adjust analytics to use schemas.
    # Actually, Pydantic schemas work similar to models for these simple properties.
    # Let's fetch models directly to be safe, since relationships like issue.symptoms might be used.
    
    from app.models.appliance import Appliance
    from app.models.issue import IssueReport
    from app.models.repair import RepairHistory
    
    app_model = db.query(Appliance).filter(Appliance.id == appliance_id).first()
    issue_models = db.query(IssueReport).filter(IssueReport.appliance_id == appliance_id).all()
    repair_models = db.query(RepairHistory).filter(RepairHistory.appliance_id == appliance_id).all()
    
    metrics = calculate_appliance_metrics(app_model, issue_models, repair_models)
    recurring = detect_recurring_problems(issue_models)
    
    return {
        "appliance_id": app_model.id,
        "name": app_model.name,
        "brand": app_model.brand,
        "model": app_model.model_number,
        "metrics": metrics,
        "recurring_problems": recurring,
        "raw_counts": {
            "issues": len(issue_models),
            "repairs": len(repair_models)
        }
    }
