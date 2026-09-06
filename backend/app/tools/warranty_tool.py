from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.models.appliance import Appliance
from app.services.repair_analytics import evaluate_warranty

def check_warranty_status(db: Session, appliance_id: int, issue_date: date = None) -> Dict[str, Any]:
    """
    Evaluates the warranty status for an appliance.
    Returns purchase date, expiry date, days remaining, and status.
    Does NOT make legal claims.
    """
    appliance = db.query(Appliance).filter(Appliance.id == appliance_id).first()
    if not appliance:
        return {"error": f"Appliance with id {appliance_id} not found."}
        
    warranty_info = evaluate_warranty(appliance, issue_date)
    
    # Format dates safely
    purchase_str = None
    if appliance.purchase_date:
        purchase_str = appliance.purchase_date.isoformat() if isinstance(appliance.purchase_date, date) else str(appliance.purchase_date)
        
    expiry_str = None
    if appliance.warranty_expiry:
        expiry = appliance.warranty_expiry
        if isinstance(expiry, datetime):
            expiry = expiry.date()
        expiry_str = expiry.isoformat()
        
    reference_date_str = (issue_date or date.today()).isoformat()
    
    return {
        "appliance_id": appliance_id,
        "reference_date": reference_date_str,
        "purchase_date": purchase_str,
        "expiry_date": expiry_str,
        "warranty_status": warranty_info.get("status", "unknown"),
        "days_remaining": warranty_info.get("days_remaining", None),
        "disclaimer": "This information is calculated based on user-provided dates and does not constitute a legal guarantee of coverage."
    }
