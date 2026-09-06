import pytest
from app.models.enums import IssueSeverity, IssueStatus, RepairOutcome
from app.models.issue import IssueReport
from app.models.symptom import Symptom
from app.models.appliance import Appliance
from app.services.history_matching_service import find_history_match
from app.schemas.appliance import ApplianceCreate
from app.schemas.issue import IssueCreate
from app.services.appliance_service import ApplianceService
from app.services.issue_service import IssueService
from app.services.repair_service import RepairService
from app.schemas.repair import RepairHistoryCreate

def setup_db(db):
    # Ensure empty db
    db.query(Symptom).delete()
    db.query(IssueReport).delete()
    db.query(Appliance).delete()
    db.commit()

def test_scenario_A_fresh_investigation(test_db):
    setup_db(test_db)
    # New issue + no history -> FRESH_INVESTIGATION
    app_in = ApplianceCreate(name="Fridge", category="refrigerator")
    app = ApplianceService.create_appliance(test_db, app_in)
    
    issue_in = IssueCreate(title="Not cooling properly", description="The fridge is warm inside.", severity=IssueSeverity.HIGH)
    issue = IssueService.create_issue(test_db, app.id, issue_in)
    
    match = find_history_match(test_db, app.id, issue)
    assert match["analysis_mode"] == "fresh_investigation"
    assert match["match_found"] is False

def test_scenario_B_historical_match(test_db):
    setup_db(test_db)
    app_in = ApplianceCreate(name="Fridge", category="refrigerator")
    app = ApplianceService.create_appliance(test_db, app_in)
    
    # Past successful issue
    past_issue = IssueService.create_issue(test_db, app.id, IssueCreate(title="Not cooling properly", description="The fridge is warm inside."))
    RepairService.add_repair_record(test_db, app.id, RepairHistoryCreate(issue_id=past_issue.id, repair_type="Parts Replacement", repair_notes="Replaced compressor", outcome=RepairOutcome.SUCCESSFUL))
    
    # Current issue
    curr_issue = IssueService.create_issue(test_db, app.id, IssueCreate(title="Not cooling properly", description="The fridge is warm inside again."))
    
    match = find_history_match(test_db, app.id, curr_issue)
    assert match["analysis_mode"] == "historical_match"
    assert match["match_found"] is True
    assert match["previous_outcome"] == "successful"

def test_scenario_C_reinvestigation_required(test_db):
    setup_db(test_db)
    app_in = ApplianceCreate(name="Fridge", category="refrigerator")
    app = ApplianceService.create_appliance(test_db, app_in)
    
    # Past failed issue
    past_issue = IssueService.create_issue(test_db, app.id, IssueCreate(title="Leaking water", description="Water on the floor."))
    RepairService.add_repair_record(test_db, app.id, RepairHistoryCreate(issue_id=past_issue.id, repair_type="Adjustment", repair_notes="Tightened hose", outcome=RepairOutcome.FAILED))
    
    # Current issue
    curr_issue = IssueService.create_issue(test_db, app.id, IssueCreate(title="Leaking water", description="Water on the floor again."))
    
    match = find_history_match(test_db, app.id, curr_issue)
    assert match["analysis_mode"] == "reinvestigation_required"
    assert match["match_found"] is True

def test_scenario_D_different_issue_fresh_investigation(test_db):
    setup_db(test_db)
    app_in = ApplianceCreate(name="Fridge", category="refrigerator")
    app = ApplianceService.create_appliance(test_db, app_in)
    
    # Past successful issue
    past_issue = IssueService.create_issue(test_db, app.id, IssueCreate(title="Leaking water", description="Water on the floor."))
    RepairService.add_repair_record(test_db, app.id, RepairHistoryCreate(issue_id=past_issue.id, repair_type="Adjustment", repair_notes="Tightened hose", outcome=RepairOutcome.SUCCESSFUL))
    
    # Current issue (completely different)
    curr_issue = IssueService.create_issue(test_db, app.id, IssueCreate(title="Ice maker broken", description="No ice being produced."))
    
    match = find_history_match(test_db, app.id, curr_issue)
    assert match["analysis_mode"] == "fresh_investigation"
    assert match["match_found"] is False
