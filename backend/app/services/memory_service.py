"""
Memory service for long-term, appliance-specific agent memory.

Stores only meaningful insights — NOT raw conversations or every analysis step.
Uses keyword-overlap deduplication. No vector database required.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.memory import AgentMemory
from app.models.enums import MemoryType


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_DEFAULT_LIMIT = 10
_HIGH_IMPORTANCE_THRESHOLD = 5.0
_DUPLICATE_OVERLAP_THRESHOLD = 0.6  # 60% keyword overlap triggers duplicate check


def _keyword_set(text: str) -> set:
    """Return a normalised set of meaningful words from text."""
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on",
                  "at", "to", "of", "and", "or", "for", "with", "has", "had",
                  "it", "this", "that", "be", "by", "from", "as", "not"}
    words = {w.lower().strip(".,;:") for w in text.split() if len(w) > 2}
    return words - stop_words


def check_duplicate_memory(
    db: Session,
    appliance_id: int,
    content: str,
    memory_type: MemoryType,
) -> Optional[AgentMemory]:
    """
    Check if a sufficiently similar memory already exists for this appliance.
    Uses keyword overlap — returns the existing memory if a duplicate is detected.
    """
    existing = (
        db.query(AgentMemory)
        .filter(
            AgentMemory.appliance_id == appliance_id,
            AgentMemory.memory_type == memory_type,
        )
        .all()
    )
    new_keywords = _keyword_set(content)
    if not new_keywords:
        return None

    for mem in existing:
        mem_keywords = _keyword_set(mem.content)
        if not mem_keywords:
            continue
        intersection = new_keywords & mem_keywords
        union = new_keywords | mem_keywords
        overlap = len(intersection) / len(union) if union else 0.0
        if overlap >= _DUPLICATE_OVERLAP_THRESHOLD:
            return mem  # duplicate found

    return None


def store_memory(
    db: Session,
    appliance_id: int,
    memory_type: MemoryType,
    content: str,
    importance_score: float = 1.0,
) -> Optional[AgentMemory]:
    """
    Persist a meaningful memory for an appliance.
    Returns None if a duplicate already exists (and updates its importance instead).
    Only stores: recurring_fault, previous_repair, appliance_behavior,
                 successful_fix, failed_fix, maintenance_pattern.
    Does NOT store raw conversations or temporary statistics.
    """
    content = content.strip()
    if not content:
        return None

    # Clamp importance score
    importance_score = max(0.0, min(10.0, importance_score))

    # Duplicate guard
    duplicate = check_duplicate_memory(db, appliance_id, content, memory_type)
    if duplicate:
        # Bump importance slightly to reflect re-confirmation
        new_score = min(10.0, duplicate.importance_score + 0.5)
        update_memory_importance(db, duplicate.id, new_score)
        mark_memory_confirmed(db, duplicate.id)
        return duplicate

    memory = AgentMemory(
        appliance_id=appliance_id,
        memory_type=memory_type,
        content=content,
        importance_score=importance_score,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def get_relevant_memories(
    db: Session,
    appliance_id: int,
    limit: int = _DEFAULT_LIMIT,
) -> List[AgentMemory]:
    """
    Return the most important memories for an appliance, ordered by importance_score desc.
    """
    return (
        db.query(AgentMemory)
        .filter(AgentMemory.appliance_id == appliance_id)
        .order_by(AgentMemory.importance_score.desc(), AgentMemory.created_at.desc())
        .limit(limit)
        .all()
    )


def get_high_importance_memories(
    db: Session,
    appliance_id: int,
    threshold: float = _HIGH_IMPORTANCE_THRESHOLD,
) -> List[AgentMemory]:
    """
    Return only memories whose importance_score meets or exceeds the threshold.
    """
    return (
        db.query(AgentMemory)
        .filter(
            AgentMemory.appliance_id == appliance_id,
            AgentMemory.importance_score >= threshold,
        )
        .order_by(AgentMemory.importance_score.desc())
        .all()
    )


def update_memory_importance(
    db: Session,
    memory_id: int,
    new_score: float,
) -> Optional[AgentMemory]:
    """Update the importance_score of an existing memory."""
    memory = db.query(AgentMemory).filter(AgentMemory.id == memory_id).first()
    if not memory:
        return None
    memory.importance_score = max(0.0, min(10.0, new_score))
    db.commit()
    db.refresh(memory)
    return memory


def mark_memory_confirmed(
    db: Session,
    memory_id: int,
) -> Optional[AgentMemory]:
    """Set last_confirmed_at to now, indicating the memory was re-observed."""
    memory = db.query(AgentMemory).filter(AgentMemory.id == memory_id).first()
    if not memory:
        return None
    memory.last_confirmed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(memory)
    return memory
