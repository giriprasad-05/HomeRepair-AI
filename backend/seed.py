"""
Database Seed Script for HomeRepair AI.

Seeds 3 realistic appliances demonstrating 8 distinct diagnostic scenarios:
1. Normal issue with enough history (LG Washer - 2 prior repairs, full metrics)
2. Insufficient historical information (Daikin AC - brand new, 0 prior repairs, 0 symptoms)
3. Recurring issue (Samsung Refrigerator - 4 occurrences of ice maker failure)
4. Failed previous repair (Samsung Refrigerator - 3 failed repair attempts)
5. Active warranty (LG Washer - purchased 8 months ago, 16 months remaining)
6. Expired warranty (Samsung Refrigerator - purchased 3 years ago, expired 2 years ago)
7. Error-code issue (LG Washer - symptom error code "UE")
8. Non-error-code issue (Samsung Refrigerator - descriptive symptoms only)

Usage:
    python seed.py [--clean]
"""
import sys
import os
from datetime import date, datetime, timedelta, timezone

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.models.enums import ApplianceCategory, IssueSeverity, IssueStatus, MemoryType
from app.models.appliance import Appliance
from app.models.issue import IssueReport
from app.models.symptom import Symptom
from app.models.repair import RepairHistory
from app.models.memory import AgentMemory


def seed_database(clean: bool = True):
    print("=" * 60)
    print("HomeRepair AI — Database Seeding")
    print("=" * 60)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        today = date.today()

        if clean:
            print("[INFO] Cleaning existing seed appliances...")
            existing_appliances = db.query(Appliance).filter(
                Appliance.model_number.in_(["WM4000HBA", "RF28R7351SR", "FTXM35R"])
            ).all()
            for app in existing_appliances:
                db.delete(app)
            db.commit()
            print("[INFO] Existing test appliances removed.")

        # -------------------------------------------------------------
        # 1. WASHING MACHINE: LG WM4000HBA
        # Scenarios:
        #   - Scenario 1: Normal issue with enough history
        #   - Scenario 5: Active warranty (purchased 8 mo ago, expires in 16 mo)
        #   - Scenario 7: Error-code issue (error code "UE")
        # -------------------------------------------------------------
        print("\n[1/3] Creating LG Front Load Washing Machine...")
        washer = Appliance(
            name="Front Load Washer",
            brand="LG",
            model_number="WM4000HBA",
            category=ApplianceCategory.WASHING_MACHINE,
            location="Laundry Room",
            purchase_date=today - timedelta(days=240),
            warranty_expiry=today + timedelta(days=490),
            notes="Smart front-load washer with TurboWash and Steam technology.",
            is_active=True,
        )
        db.add(washer)
        db.flush()

        # Prior resolved issue 1
        w_issue_1 = IssueReport(
            appliance_id=washer.id,
            title="Excessive Drain Noise",
            description="Loud gurgling noise when the drain pump activates during rinse cycle.",
            severity=IssueSeverity.MEDIUM,
            status=IssueStatus.RESOLVED,
            reported_at=datetime.now(timezone.utc) - timedelta(days=180),
            resolved_at=datetime.now(timezone.utc) - timedelta(days=178),
        )
        db.add(w_issue_1)
        db.flush()

        db.add(Symptom(
            issue_id=w_issue_1.id,
            name="Drain Noise",
            value="78",
            unit="dB",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=180),
        ))

        db.add(RepairHistory(
            appliance_id=washer.id,
            issue_id=w_issue_1.id,
            repair_type="Drain Pump Cleaning",
            description="Removed coin trap cover, extracted hair pin and sediment blocking impeller.",
            parts_replaced="Pump filter gasket",
            service_cost=85.0,
            repair_date=today - timedelta(days=178),
            outcome="Successful - pump draining quietly at standard speed.",
        ))

        # Prior resolved issue 2
        w_issue_2 = IssueReport(
            appliance_id=washer.id,
            title="Slow Water Intake",
            description="Water taking over 15 minutes to fill drum on normal cold wash.",
            severity=IssueSeverity.LOW,
            status=IssueStatus.RESOLVED,
            reported_at=datetime.now(timezone.utc) - timedelta(days=90),
            resolved_at=datetime.now(timezone.utc) - timedelta(days=88),
        )
        db.add(w_issue_2)
        db.flush()

        db.add(Symptom(
            issue_id=w_issue_2.id,
            name="Fill Rate",
            value="Restricted flow",
            unit="gpm",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=90),
        ))

        db.add(RepairHistory(
            appliance_id=washer.id,
            issue_id=w_issue_2.id,
            repair_type="Inlet Filter Cleanse",
            description="Cleaned mineral buildup and sediment from cold water inlet valve mesh screens.",
            parts_replaced=None,
            service_cost=65.0,
            repair_date=today - timedelta(days=88),
            outcome="Successful - full inlet pressure restored.",
        ))

        # Active Issue: Error Code UE (Scenarios 1 & 7)
        w_issue_active = IssueReport(
            appliance_id=washer.id,
            title="Spin Cycle Vibration and Error Code UE",
            description="Drum shakes violently when entering the high-speed extraction cycle, aborts spin, and displays code UE on LED panel.",
            severity=IssueSeverity.HIGH,
            status=IssueStatus.OPEN,
            reported_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.add(w_issue_active)
        db.flush()

        db.add(Symptom(
            issue_id=w_issue_active.id,
            name="Error Code",
            value="UE",
            unit=None,
            recorded_at=datetime.now(timezone.utc) - timedelta(days=1),
        ))
        db.add(Symptom(
            issue_id=w_issue_active.id,
            name="Vibration Level",
            value="Severe shaking during spin ramp-up",
            unit=None,
            recorded_at=datetime.now(timezone.utc) - timedelta(days=1),
        ))

        # Memories for LG Washer
        db.add(AgentMemory(
            appliance_id=washer.id,
            memory_type=MemoryType.APPLIANCE_BEHAVIOR,
            content="Appliance is sensitive to uneven weight distribution during bulky bedding cycles.",
            importance_score=7.0,
            created_at=datetime.now(timezone.utc) - timedelta(days=80),
        ))
        db.add(AgentMemory(
            appliance_id=washer.id,
            memory_type=MemoryType.SUCCESSFUL_FIX,
            content="Clearing cold water inlet screen resolved fill-time delay previously.",
            importance_score=6.5,
            created_at=datetime.now(timezone.utc) - timedelta(days=88),
        ))

        # -------------------------------------------------------------
        # 2. REFRIGERATOR: Samsung RF28R7351SR
        # Scenarios:
        #   - Scenario 3: Recurring issue (4 occurrences of Ice Maker failure)
        #   - Scenario 4: Failed previous repair (3 failed repair attempts)
        #   - Scenario 6: Expired warranty (purchased 3 yrs ago, expired 2 yrs ago)
        #   - Scenario 8: Non-error-code issue (physical symptoms, no error codes)
        # -------------------------------------------------------------
        print("[2/3] Creating Samsung French Door Refrigerator...")
        fridge = Appliance(
            name="French Door Refrigerator",
            brand="Samsung",
            model_number="RF28R7351SR",
            category=ApplianceCategory.REFRIGERATOR,
            location="Kitchen",
            purchase_date=today - timedelta(days=1100),
            warranty_expiry=today - timedelta(days=735),
            notes="3-Door French Door Refrigerator with Twin Cooling Plus and Ice Master.",
            is_active=True,
        )
        db.add(fridge)
        db.flush()

        # Recurring Issue 1 (18 months ago)
        f_issue_1 = IssueReport(
            appliance_id=fridge.id,
            title="Ice Maker Frost Buildup and Jam",
            description="Ice room compartment has frost buildup, dispenser lever clicks without dispensing.",
            severity=IssueSeverity.MEDIUM,
            status=IssueStatus.RESOLVED,
            reported_at=datetime.now(timezone.utc) - timedelta(days=540),
            resolved_at=datetime.now(timezone.utc) - timedelta(days=535),
        )
        db.add(f_issue_1)
        db.flush()

        db.add(Symptom(
            issue_id=f_issue_1.id,
            name="Frost Accumulation",
            value="Moderate frost in ice bucket",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=540),
        ))
        db.add(RepairHistory(
            appliance_id=fridge.id,
            issue_id=f_issue_1.id,
            repair_type="Defrost Reset & Seal Adjustment",
            description="Manual forced defrost of ice maker compartment and adjusted flapper gasket.",
            parts_replaced=None,
            service_cost=110.0,
            repair_date=today - timedelta(days=535),
            outcome="Unsuccessful - temporary fix, frost returned within 30 days.",
        ))

        # Recurring Issue 2 (10 months ago)
        f_issue_2 = IssueReport(
            appliance_id=fridge.id,
            title="Ice Maker Frost Buildup and Jam",
            description="Ice room iced over again, auger motor stalled.",
            severity=IssueSeverity.HIGH,
            status=IssueStatus.RESOLVED,
            reported_at=datetime.now(timezone.utc) - timedelta(days=300),
            resolved_at=datetime.now(timezone.utc) - timedelta(days=295),
        )
        db.add(f_issue_2)
        db.flush()

        db.add(Symptom(
            issue_id=f_issue_2.id,
            name="Frost Accumulation",
            value="Ice sheet covering auger shaft",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=300),
        ))
        db.add(RepairHistory(
            appliance_id=fridge.id,
            issue_id=f_issue_2.id,
            repair_type="Auger Motor Replacement",
            description="Replaced ice dispenser auger motor assembly.",
            parts_replaced="Auger Motor Assembly DA97-12540G",
            service_cost=275.0,
            repair_date=today - timedelta(days=295),
            outcome="Failed repair - auger replaced but iced up solid within 6 weeks.",
        ))

        # Recurring Issue 3 (4 months ago)
        f_issue_3 = IssueReport(
            appliance_id=fridge.id,
            title="Ice Maker Frost Buildup and Jam",
            description="Ice bucket locked solid, water dripping from ice chute into crisper drawer.",
            severity=IssueSeverity.HIGH,
            status=IssueStatus.RESOLVED,
            reported_at=datetime.now(timezone.utc) - timedelta(days=120),
            resolved_at=datetime.now(timezone.utc) - timedelta(days=115),
        )
        db.add(f_issue_3)
        db.flush()

        db.add(Symptom(
            issue_id=f_issue_3.id,
            name="Frost Accumulation",
            value="Solid block of ice around tray",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=120),
        ))
        db.add(Symptom(
            issue_id=f_issue_3.id,
            name="Water Leakage",
            value="Water pooling in deli drawer",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=120),
        ))
        db.add(RepairHistory(
            appliance_id=fridge.id,
            issue_id=f_issue_3.id,
            repair_type="Ice Maker Assembly Replacement",
            description="Installed updated ice maker kit and silicone sealant on cabin joint.",
            parts_replaced="Ice Maker Assembly DA97-15217D",
            service_cost=340.0,
            repair_date=today - timedelta(days=115),
            outcome="Failed repair - moisture infiltration persists through cabin seams.",
        ))

        # Active Issue: Recurring, Failed Fixes, Expired Warranty, Non-Error Code (Scenarios 3, 4, 6, 8)
        f_issue_active = IssueReport(
            appliance_id=fridge.id,
            title="Ice Maker Frost Buildup and Jam",
            description="Ice room is completely frozen solid again. Ice bucket cannot be pulled out and water is dripping into the fresh food compartment.",
            severity=IssueSeverity.HIGH,
            status=IssueStatus.OPEN,
            reported_at=datetime.now(timezone.utc) - timedelta(days=2),
        )
        db.add(f_issue_active)
        db.flush()

        db.add(Symptom(
            issue_id=f_issue_active.id,
            name="Frost Accumulation",
            value="Heavy frost encasing ice bucket and auger",
            unit=None,
            recorded_at=datetime.now(timezone.utc) - timedelta(days=2),
        ))
        db.add(Symptom(
            issue_id=f_issue_active.id,
            name="Water Leakage",
            value="Continuous water dripping into vegetable drawer",
            unit="ml/hr",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=2),
        ))
        db.add(Symptom(
            issue_id=f_issue_active.id,
            name="Ice Dispenser Jammed",
            value="Dispenser flap motor buzzing without moving",
            unit=None,
            recorded_at=datetime.now(timezone.utc) - timedelta(days=2),
        ))

        # Memories for Samsung Refrigerator
        db.add(AgentMemory(
            appliance_id=fridge.id,
            memory_type=MemoryType.RECURRING_FAULT,
            content="Repeated freeze-up in ice maker compartment caused by warm air infiltration around cabinet seam seal.",
            importance_score=8.5,
            created_at=datetime.now(timezone.utc) - timedelta(days=115),
        ))
        db.add(AgentMemory(
            appliance_id=fridge.id,
            memory_type=MemoryType.FAILED_FIX,
            content="Replacing auger motor and ice bucket did not stop frost because cabinet air leak remained unsealed.",
            importance_score=8.0,
            created_at=datetime.now(timezone.utc) - timedelta(days=115),
        ))

        # -------------------------------------------------------------
        # 3. AIR CONDITIONER: Daikin FTXM35R
        # Scenarios:
        #   - Scenario 2: Insufficient historical information (0 prior repairs, 0 symptoms)
        # -------------------------------------------------------------
        print("[3/3] Creating Daikin Inverter Air Conditioner...")
        ac = Appliance(
            name="Inverter Split AC",
            brand="Daikin",
            model_number="FTXM35R",
            category=ApplianceCategory.AIR_CONDITIONER,
            location="Master Bedroom",
            purchase_date=today - timedelta(days=10),
            warranty_expiry=today + timedelta(days=1815),
            notes="Brand new wall-mounted inverter split AC unit with heat pump.",
            is_active=True,
        )
        db.add(ac)
        db.flush()

        # Active Issue with NO recorded symptoms and NO prior history
        # Triggers insufficient data route and uncertainty explanation
        ac_issue_active = IssueReport(
            appliance_id=ac.id,
            title="Unusual Warm Odor on Startup",
            description="Faint warm plastic smell noticed briefly when starting heat mode on chilly mornings.",
            severity=IssueSeverity.LOW,
            status=IssueStatus.OPEN,
            reported_at=datetime.now(timezone.utc) - timedelta(hours=8),
        )
        db.add(ac_issue_active)
        db.flush()

        # NOTE: Intentionally NO symptoms and NO prior repairs added.
        # This makes the agent's behavior visibly different:
        # It flags insufficient evidence, identifies missing symptoms, and halts before hallucinating causes!

        db.commit()

        print("\n" + "=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"[Appliance 1] {washer.brand} {washer.name} (#{washer.id})")
        print(f"  - Active Issue #{w_issue_active.id}: '{w_issue_active.title}'")
        print(f"  - Demonstrates: [1] Normal History, [5] Active Warranty, [7] Error-code UE")
        print(f"[Appliance 2] {fridge.brand} {fridge.name} (#{fridge.id})")
        print(f"  - Active Issue #{f_issue_active.id}: '{f_issue_active.title}'")
        print(f"  - Demonstrates: [3] Recurring Issue, [4] Failed Repairs, [6] Expired Warranty, [8] Non-error-code")
        print(f"[Appliance 3] {ac.brand} {ac.name} (#{ac.id})")
        print(f"  - Active Issue #{ac_issue_active.id}: '{ac_issue_active.title}'")
        print(f"  - Demonstrates: [2] Insufficient Historical Information (0 symptoms, 0 repairs)")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clean_flag = "--no-clean" not in sys.argv
    seed_database(clean=clean_flag)
