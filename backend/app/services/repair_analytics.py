from typing import List, Dict, Any
from datetime import datetime, date, timezone
from collections import Counter
from app.models.appliance import Appliance
from app.models.issue import IssueReport
from app.models.repair import RepairHistory
from app.models.enums import IssueStatus

def calculate_appliance_metrics(appliance: Appliance, issues: List[IssueReport], repairs: List[RepairHistory]) -> Dict[str, Any]:
    """Calculate deterministic metrics for an appliance."""
    total_issues = len(issues)
    open_issues = len([i for i in issues if i.status != IssueStatus.RESOLVED])
    resolved_issues = len([i for i in issues if i.status == IssueStatus.RESOLVED])
    repair_count = len(repairs)
    
    total_repair_cost = sum(r.service_cost for r in repairs if r.service_cost is not None)
    average_repair_cost = total_repair_cost / repair_count if repair_count > 0 else 0.0
    
    # Most common issue title
    most_common_title = None
    if issues:
        title_counts = Counter(i.title for i in issues)
        most_common_title = title_counts.most_common(1)[0][0]
        
    most_frequent_symptom = None
    symptom_list = []
    for issue in issues:
        for symptom in issue.symptoms:
            symptom_list.append(symptom.name)
    if symptom_list:
        symptom_counts = Counter(symptom_list)
        most_frequent_symptom = symptom_counts.most_common(1)[0][0]
        
    days_since_last_repair = None
    repairs_with_date = [r for r in repairs if r.repair_date is not None]
    if repairs_with_date:
        latest_repair = max(r.repair_date for r in repairs_with_date)
        if isinstance(latest_repair, datetime):
            latest_repair_date = latest_repair.date()
        else:
            latest_repair_date = latest_repair
            
        days_since_last_repair = (date.today() - latest_repair_date).days
        
    warranty_status = evaluate_warranty(appliance)
    
    return {
        "total_issues": total_issues,
        "open_issues": open_issues,
        "resolved_issues": resolved_issues,
        "repair_count": repair_count,
        "total_repair_cost": float(total_repair_cost),
        "average_repair_cost": float(average_repair_cost),
        "most_common_issue": most_common_title,
        "most_frequent_symptom": most_frequent_symptom,
        "days_since_last_repair": days_since_last_repair,
        "warranty_status": warranty_status["status"]
    }

def detect_recurring_problems(issues: List[IssueReport]) -> List[Dict[str, Any]]:
    """Detect repeated issue titles or symptoms."""
    recurring_problems = []
    
    title_counts = Counter(i.title for i in issues)
    for title, count in title_counts.items():
        if count >= 3:
            recurring_problems.append({
                "type": "issue_title",
                "pattern": title,
                "occurrence_count": count,
                "recurring": True
            })
            
    symptom_list = []
    for issue in issues:
        for symptom in issue.symptoms:
            symptom_list.append(symptom.name)
            
    symptom_counts = Counter(symptom_list)
    for symptom_name, count in symptom_counts.items():
        if count >= 3:
            recurring_problems.append({
                "type": "symptom",
                "pattern": symptom_name,
                "occurrence_count": count,
                "recurring": True
            })
            
    return recurring_problems

def analyze_repair_outcomes(repairs: List[RepairHistory]) -> Dict[str, Any]:
    """Detect successful, failed, partially resolved repairs based on follow-up issues."""
    successful = 0
    failed = 0
    
    repair_types_failure_counts = Counter()
    
    for repair in repairs:
        is_failed = False
        if getattr(repair, 'successful', True) is False:
            is_failed = True
        outcome = (getattr(repair, 'outcome', None) or "").lower()
        if outcome and any(word in outcome for word in ["fail", "unsuccessful", "incomplete", "partial"]):
            is_failed = True

        if is_failed:
            failed += 1
            repair_types_failure_counts[repair.repair_type or 'unknown'] += 1
        else:
            successful += 1
            
    warnings = []
    for rtype, count in repair_types_failure_counts.items():
        if count >= 2:
            warnings.append(f"Repair type '{rtype}' has failed {count} times.")
            
    return {
        "successful_repairs": successful,
        "failed_repairs": failed,
        "partially_resolved": 0,
        "warnings": warnings
    }

def evaluate_warranty(appliance: Appliance, issue_date: date = None) -> Dict[str, Any]:
    """Calculate warranty status."""
    if not appliance.purchase_date and not appliance.warranty_expiry:
        return {"status": "unknown"}
        
    reference_date = issue_date or date.today()
    
    if appliance.warranty_expiry:
        expiry = appliance.warranty_expiry
        if isinstance(expiry, datetime):
            expiry = expiry.date()
            
        days_remaining = (expiry - reference_date).days
        
        if days_remaining < 0:
            return {"status": "expired", "days_remaining": days_remaining}
        elif days_remaining <= 30: # 30 days configurable threshold
            return {"status": "expiring_soon", "days_remaining": days_remaining}
        else:
            return {"status": "active", "days_remaining": days_remaining}
            
    return {"status": "unknown"}
