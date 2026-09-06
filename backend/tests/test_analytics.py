from datetime import date, timedelta
import pytest
from app.models.enums import ApplianceCategory, IssueSeverity, IssueStatus
from app.models.appliance import Appliance
from app.models.issue import IssueReport
from app.models.symptom import Symptom
from app.models.repair import RepairHistory
from app.services.repair_analytics import (
    calculate_appliance_metrics,
    detect_recurring_problems,
    analyze_repair_outcomes,
    evaluate_warranty,
)


def test_calculate_appliance_metrics():
    today = date.today()
    appliance = Appliance(
        id=1,
        name="Test Washer",
        brand="LG",
        category=ApplianceCategory.WASHING_MACHINE,
        purchase_date=today - timedelta(days=100),
        warranty_expiry=today + timedelta(days=265),
    )

    issue1 = IssueReport(id=1, appliance_id=1, title="Drain Issue", status=IssueStatus.RESOLVED)
    issue2 = IssueReport(id=2, appliance_id=1, title="Drain Issue", status=IssueStatus.OPEN)
    issue1.symptoms = [Symptom(name="Slow Drain", value="Yes")]
    issue2.symptoms = [Symptom(name="Slow Drain", value="Yes")]

    repair1 = RepairHistory(id=1, appliance_id=1, repair_type="Clean Pump", service_cost=100.0, repair_date=today - timedelta(days=20))
    repair2 = RepairHistory(id=2, appliance_id=1, repair_type="Replace Hose", service_cost=50.0, repair_date=today - timedelta(days=5))

    metrics = calculate_appliance_metrics(appliance, [issue1, issue2], [repair1, repair2])

    assert metrics["total_issues"] == 2
    assert metrics["open_issues"] == 1
    assert metrics["resolved_issues"] == 1
    assert metrics["repair_count"] == 2
    assert metrics["total_repair_cost"] == 150.0
    assert metrics["average_repair_cost"] == 75.0
    assert metrics["most_common_issue"] == "Drain Issue"
    assert metrics["most_frequent_symptom"] == "Slow Drain"
    assert metrics["days_since_last_repair"] == 5
    assert metrics["warranty_status"] == "active"


def test_detect_recurring_problems():
    # 3 occurrences of same title and symptom -> triggers recurring
    issues = []
    for i in range(3):
        iss = IssueReport(id=i+1, title="Ice Maker Jam", status=IssueStatus.OPEN)
        iss.symptoms = [Symptom(name="Frost Buildup", value="Heavy")]
        issues.append(iss)

    recurring = detect_recurring_problems(issues)
    patterns = [r["pattern"] for r in recurring]
    assert "Ice Maker Jam" in patterns
    assert "Frost Buildup" in patterns
    for r in recurring:
        assert r["recurring"] is True
        assert r["occurrence_count"] >= 3


def test_analyze_repair_outcomes_detection():
    repairs = [
        RepairHistory(id=1, repair_type="Motor Fix", outcome="Successful fix"),
        RepairHistory(id=2, repair_type="Motor Fix", outcome="Failed repair - motor stalled"),
        RepairHistory(id=3, repair_type="Motor Fix", outcome="Unsuccessful fix - failed again"),
    ]

    result = analyze_repair_outcomes(repairs)
    assert result["successful_repairs"] == 1
    assert result["failed_repairs"] == 2
    assert len(result["warnings"]) == 1
    assert "Motor Fix" in result["warnings"][0]


def test_evaluate_warranty_states():
    today = date.today()

    # Active (> 30 days)
    app_active = Appliance(purchase_date=today - timedelta(days=100), warranty_expiry=today + timedelta(days=100))
    res_active = evaluate_warranty(app_active)
    assert res_active["status"] == "active"
    assert res_active["days_remaining"] == 100

    # Expiring soon (1 to 30 days)
    app_soon = Appliance(purchase_date=today - timedelta(days=350), warranty_expiry=today + timedelta(days=15))
    res_soon = evaluate_warranty(app_soon)
    assert res_soon["status"] == "expiring_soon"
    assert res_soon["days_remaining"] == 15

    # Expired (< 0 days)
    app_expired = Appliance(purchase_date=today - timedelta(days=500), warranty_expiry=today - timedelta(days=50))
    res_expired = evaluate_warranty(app_expired)
    assert res_expired["status"] == "expired"
    assert res_expired["days_remaining"] < 0

    # Unknown
    app_unknown = Appliance(purchase_date=None, warranty_expiry=None)
    res_unknown = evaluate_warranty(app_unknown)
    assert res_unknown["status"] == "unknown"
