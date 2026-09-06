import pytest
from app.models.enums import ApplianceCategory, MemoryType
from app.models.appliance import Appliance
from app.services.memory_service import (
    store_memory,
    get_relevant_memories,
    get_high_importance_memories,
    check_duplicate_memory,
    update_memory_importance,
    mark_memory_confirmed,
)


def test_memory_storage_and_retrieval(test_db):
    app = Appliance(name="Washer", brand="LG", category=ApplianceCategory.WASHING_MACHINE)
    test_db.add(app)
    test_db.commit()

    m1 = store_memory(
        db=test_db,
        appliance_id=app.id,
        memory_type=MemoryType.RECURRING_FAULT,
        content="Drain pump gets clogged by lint and coins frequently.",
        importance_score=8.0,
    )
    assert m1 is not None
    assert m1.id is not None
    assert m1.importance_score == 8.0

    m2 = store_memory(
        db=test_db,
        appliance_id=app.id,
        memory_type=MemoryType.SUCCESSFUL_FIX,
        content="Cleaning the lint trap solved vibration.",
        importance_score=5.0,
    )

    memories = get_relevant_memories(test_db, app.id)
    assert len(memories) == 2
    # Highest importance first
    assert memories[0].importance_score >= memories[1].importance_score

    # High importance filter
    high = get_high_importance_memories(test_db, app.id, threshold=7.0)
    assert len(high) == 1
    assert high[0].importance_score == 8.0


def test_memory_duplicate_prevention(test_db):
    app = Appliance(name="Fridge", brand="Samsung", category=ApplianceCategory.REFRIGERATOR)
    test_db.add(app)
    test_db.commit()

    # Original memory
    m1 = store_memory(
        db=test_db,
        appliance_id=app.id,
        memory_type=MemoryType.RECURRING_FAULT,
        content="Ice maker freezes over due to air leaking from cabinet door seam.",
        importance_score=7.0,
    )
    assert m1 is not None

    # Near-identical text with high keyword overlap
    duplicate = store_memory(
        db=test_db,
        appliance_id=app.id,
        memory_type=MemoryType.RECURRING_FAULT,
        content="Ice maker freezes over because air leaks through cabinet door seam.",
        importance_score=6.0,
    )

    # Should detect duplicate and return updated existing memory instead of creating a new row
    assert duplicate.id == m1.id
    # Duplicate re-confirmation boosts score
    assert duplicate.importance_score >= 7.0
    assert duplicate.last_confirmed_at is not None

    all_memories = get_relevant_memories(test_db, app.id)
    assert len(all_memories) == 1


def test_memory_importance_clamping_and_updates(test_db):
    app = Appliance(name="AC", brand="Daikin", category=ApplianceCategory.AIR_CONDITIONER)
    test_db.add(app)
    test_db.commit()

    # Score clamped between 0 and 10
    m = store_memory(
        db=test_db,
        appliance_id=app.id,
        memory_type=MemoryType.APPLIANCE_BEHAVIOR,
        content="Runs noisy on heat cycle startup.",
        importance_score=15.0,  # exceeds max
    )
    assert m.importance_score == 10.0

    updated = update_memory_importance(test_db, m.id, -5.0)
    assert updated.importance_score == 0.0
