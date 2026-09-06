from datetime import date, timedelta
import pytest
from app.models.enums import ApplianceCategory, IssueSeverity, IssueStatus
from app.models.appliance import Appliance
from app.models.issue import IssueReport
from app.models.symptom import Symptom
from app.models.repair import RepairHistory

from app.tools.appliance_history_tool import get_appliance_history
from app.tools.symptom_pattern_tool import analyze_symptom_patterns
from app.tools.repair_outcome_tool import analyze_repair_outcomes
from app.tools.warranty_tool import check_warranty_status
from app.tools.manual_lookup_tool import lookup_error_code


def test_appliance_history_tool(test_db):
    app = Appliance(name="Washer", brand="LG", model_number="WM1", category=ApplianceCategory.WASHING_MACHINE)
    test_db.add(app)
    test_db.commit()

    iss = IssueReport(appliance_id=app.id, title="Noise", status=IssueStatus.OPEN)
    rep = RepairHistory(appliance_id=app.id, repair_type="Belt", service_cost=90.0)
    test_db.add_all([iss, rep])
    test_db.commit()

    res = get_appliance_history(test_db, app.id)
    assert res["appliance_id"] == app.id
    assert res["raw_counts"]["issues"] == 1
    assert res["raw_counts"]["repairs"] == 1
    assert "metrics" in res


def test_symptom_pattern_tool(test_db):
    app = Appliance(name="Fridge", brand="Samsung", category=ApplianceCategory.REFRIGERATOR)
    test_db.add(app)
    test_db.commit()

    # Prior issue with symptom "Frost"
    iss1 = IssueReport(appliance_id=app.id, title="Issue 1")
    test_db.add(iss1)
    test_db.flush()
    s1 = Symptom(issue_id=iss1.id, name="Frost", value="High")
    test_db.add(s1)

    # Current issue with "Frost" and "New Noise"
    iss2 = IssueReport(appliance_id=app.id, title="Issue 2")
    test_db.add(iss2)
    test_db.flush()
    s2 = Symptom(issue_id=iss2.id, name="Frost", value="High")
    s3 = Symptom(issue_id=iss2.id, name="New Noise", value="Clicking")
    test_db.add_all([s2, s3])
    test_db.commit()

    analysis = analyze_symptom_patterns(test_db, iss2.id)
    assert analysis["issue_id"] == iss2.id
    assert len(analysis["known_symptoms_repeated"]) == 1
    assert analysis["known_symptoms_repeated"][0]["symptom"] == "Frost"
    assert "New Noise" in analysis["unusual_new_symptoms"]
    assert analysis["historical_match_confidence"] == "medium"


def test_repair_outcome_tool(test_db):
    app = Appliance(name="AC", brand="Daikin", category=ApplianceCategory.AIR_CONDITIONER)
    test_db.add(app)
    test_db.commit()

    today = date.today()
    rep1 = RepairHistory(appliance_id=app.id, repair_type="Filter", outcome="Completed successfully", repair_date=today - timedelta(days=60))
    rep2 = RepairHistory(appliance_id=app.id, repair_type="Filter", outcome="Failed fix", repair_date=today - timedelta(days=10))
    test_db.add_all([rep1, rep2])
    test_db.commit()

    outcomes = analyze_repair_outcomes(test_db, app.id)
    assert outcomes["total_repairs"] == 2
    assert outcomes["successful_fixes"] == 1
    assert outcomes["failed_fixes"] == 1
    assert len(outcomes["recurrence_analysis"]) == 1
    assert outcomes["recurrence_analysis"][0]["repair_type"] == "Filter"


def test_warranty_tool(test_db):
    today = date.today()
    app = Appliance(name="Washer", brand="LG", category=ApplianceCategory.WASHING_MACHINE, purchase_date=today - timedelta(days=60), warranty_expiry=today + timedelta(days=300))
    test_db.add(app)
    test_db.commit()

    status = check_warranty_status(test_db, app.id)
    assert status["warranty_status"] == "active"
    assert status["days_remaining"] == 300
    assert "disclaimer" in status


def test_manual_lookup_tool():
    # Known exact match: LG washing machine error UE
    lg_ue = lookup_error_code("LG", "washing_machine", "UE")
    assert lg_ue["found"] is True
    assert any("Unbalanced load" in m["possible_meaning"] for m in lg_ue["matches"])

    # Known Samsung refrigerator error E1
    samsung_e1 = lookup_error_code("Samsung", "refrigerator", "E1")
    assert samsung_e1["found"] is True
    assert any("Defrost sensor" in m["possible_meaning"] for m in samsung_e1["matches"])

    # Unknown code
    unknown = lookup_error_code("LG", "washing_machine", "XYZ999")
    assert unknown["found"] is False
