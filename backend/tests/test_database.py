from datetime import date, datetime, timezone
import pytest
from app.models.enums import ApplianceCategory, IssueSeverity, IssueStatus, MemoryType
from app.models.appliance import Appliance
from app.models.issue import IssueReport
from app.models.symptom import Symptom
from app.models.repair import RepairHistory
from app.models.memory import AgentMemory


def test_appliance_creation_and_query(test_db):
    appliance = Appliance(
        name="Test Refrigerator",
        brand="Samsung",
        model_number="RF28R",
        category=ApplianceCategory.REFRIGERATOR,
        location="Kitchen",
        purchase_date=date(2023, 1, 1),
        warranty_expiry=date(2025, 1, 1),
        notes="Primary kitchen fridge",
        is_active=True,
    )
    test_db.add(appliance)
    test_db.commit()

    saved = test_db.query(Appliance).filter(Appliance.model_number == "RF28R").first()
    assert saved is not None
    assert saved.name == "Test Refrigerator"
    assert saved.brand == "Samsung"
    assert saved.category == ApplianceCategory.REFRIGERATOR
    assert saved.is_active is True


def test_relationships_and_cascades(test_db):
    # 1. Create Appliance
    appliance = Appliance(
        name="Test Washer",
        brand="LG",
        model_number="WM4000",
        category=ApplianceCategory.WASHING_MACHINE,
        is_active=True,
    )
    test_db.add(appliance)
    test_db.commit()

    # 2. Create Issue linked to Appliance
    issue = IssueReport(
        appliance_id=appliance.id,
        title="Drum Vibration",
        description="Shaking violently",
        severity=IssueSeverity.HIGH,
        status=IssueStatus.OPEN,
    )
    test_db.add(issue)
    test_db.commit()

    # 3. Create Symptom linked to Issue
    symptom = Symptom(
        issue_id=issue.id,
        name="Error Code",
        value="UE",
    )
    test_db.add(symptom)
    test_db.commit()

    # 4. Create RepairHistory linked to Appliance and Issue
    repair = RepairHistory(
        appliance_id=appliance.id,
        issue_id=issue.id,
        repair_type="Belt Replacement",
        service_cost=120.0,
        outcome="Successful",
    )
    test_db.add(repair)
    test_db.commit()

    # 5. Create AgentMemory linked to Appliance
    memory = AgentMemory(
        appliance_id=appliance.id,
        memory_type=MemoryType.APPLIANCE_BEHAVIOR,
        content="Sensitive to unbalanced loads",
        importance_score=7.5,
    )
    test_db.add(memory)
    test_db.commit()

    # Test bidirectional relationships
    test_db.refresh(appliance)
    assert len(appliance.issues) == 1
    assert appliance.issues[0].title == "Drum Vibration"
    assert len(appliance.issues[0].symptoms) == 1
    assert appliance.issues[0].symptoms[0].name == "Error Code"
    assert len(appliance.repairs) == 1
    assert appliance.repairs[0].repair_type == "Belt Replacement"
    assert len(appliance.memories) == 1
    assert appliance.memories[0].content == "Sensitive to unbalanced loads"

    # Test Cascade Delete
    test_db.delete(appliance)
    test_db.commit()

    assert test_db.query(Appliance).count() == 0
    assert test_db.query(IssueReport).count() == 0
    assert test_db.query(Symptom).count() == 0
    assert test_db.query(RepairHistory).count() == 0
    assert test_db.query(AgentMemory).count() == 0


def test_complex_queries(test_db):
    app1 = Appliance(name="AC", brand="Daikin", category=ApplianceCategory.AIR_CONDITIONER, is_active=True)
    app2 = Appliance(name="Old Fridge", brand="Whirlpool", category=ApplianceCategory.REFRIGERATOR, is_active=False)
    test_db.add_all([app1, app2])
    test_db.commit()

    active_appliances = test_db.query(Appliance).filter(Appliance.is_active.is_(True)).all()
    assert len(active_appliances) == 1
    assert active_appliances[0].brand == "Daikin"

    by_category = test_db.query(Appliance).filter(Appliance.category == ApplianceCategory.REFRIGERATOR).all()
    assert len(by_category) == 1
    assert by_category[0].brand == "Whirlpool"
