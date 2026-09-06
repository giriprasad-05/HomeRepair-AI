from typing import Dict, Any, List
from sqlalchemy.orm import Session
from collections import Counter
from app.models.issue import IssueReport
from app.models.symptom import Symptom

def analyze_symptom_patterns(db: Session, issue_id: int) -> Dict[str, Any]:
    """
    Analyzes current symptoms for an issue and compares them 
    against historical symptoms for the same appliance.
    """
    current_issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not current_issue:
        return {"error": f"Issue with id {issue_id} not found."}
        
    appliance_id = current_issue.appliance_id
    
    # Get all previous issues for this appliance
    historical_issues = db.query(IssueReport).filter(
        IssueReport.appliance_id == appliance_id,
        IssueReport.id != issue_id
    ).all()
    
    current_symptoms = [s.name for s in db.query(Symptom).filter(Symptom.issue_id == issue_id).all()]
    if not current_symptoms:
        return {
            "current_symptoms": [],
            "historical_matches": [],
            "message": "No symptoms recorded for the current issue."
        }
        
    historical_symptom_counts = Counter()
    for hist_issue in historical_issues:
        for s in db.query(Symptom).filter(Symptom.issue_id == hist_issue.id).all():
            historical_symptom_counts[s.name] += 1
            
    matches = []
    unusual = []
    
    for symptom in current_symptoms:
        count = historical_symptom_counts.get(symptom, 0)
        if count > 0:
            matches.append({"symptom": symptom, "previous_occurrences": count})
        else:
            unusual.append(symptom)
            
    confidence = "low"
    if len(matches) > 0 and len(unusual) == 0:
        confidence = "high"
    elif len(matches) > 0:
        confidence = "medium"
        
    return {
        "issue_id": issue_id,
        "current_symptoms": current_symptoms,
        "known_symptoms_repeated": matches,
        "unusual_new_symptoms": unusual,
        "historical_match_confidence": confidence
    }
