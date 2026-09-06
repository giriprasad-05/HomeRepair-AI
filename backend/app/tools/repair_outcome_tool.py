from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.models.repair import RepairHistory

def analyze_repair_outcomes(db: Session, appliance_id: int) -> Dict[str, Any]:
    """
    Analyzes all past repairs for a given appliance.
    Returns statistics on repair types, success rates, and recurrence.
    """
    repairs = db.query(RepairHistory).filter(RepairHistory.appliance_id == appliance_id).all()
    
    if not repairs:
        return {
            "appliance_id": appliance_id,
            "message": "No repair history found for this appliance."
        }
        
    repair_types = set()
    successful = 0
    failed = 0
    
    # We will approximate recurrence if there are multiple repairs of the same type.
    # In a fully robust system, this would link to specific issues.
    type_dates = {}
    
    for repair in repairs:
        rtype = repair.repair_type or "General"
        repair_types.add(rtype)
        
        is_successful = True
        outcome = (repair.outcome or "").lower()
        if outcome and any(word in outcome for word in ["fail", "unsuccessful", "incomplete", "partial"]):
            is_successful = False
            
        if is_successful:
            successful += 1
        else:
            failed += 1
            
        if rtype not in type_dates:
            type_dates[rtype] = []
            
        r_date = repair.repair_date
        if r_date is None:
            continue
        if isinstance(r_date, datetime):
            r_date = r_date.date()
        type_dates[rtype].append(r_date)
        
    recurrence_data = []
    
    for rtype, dates in type_dates.items():
        if len(dates) > 1:
            dates_sorted = sorted(d for d in dates if d is not None)
            if len(dates_sorted) < 2:
                continue
            diffs = [(dates_sorted[i] - dates_sorted[i-1]).days for i in range(1, len(dates_sorted))]
            avg_days = sum(diffs) / len(diffs)
            recurrence_data.append({
                "repair_type": rtype,
                "occurrences": len(dates_sorted),
                "average_days_before_recurrence": round(avg_days, 1)
            })
            
    return {
        "appliance_id": appliance_id,
        "total_repairs": len(repairs),
        "repair_types_attempted": list(repair_types),
        "successful_fixes": successful,
        "failed_fixes": failed,
        "recurrence_analysis": recurrence_data
    }
