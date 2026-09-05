"""Pydantic Schemas for HomeRepair AI."""
from app.models.enums import ApplianceCategory, IssueSeverity, IssueStatus, MemoryType

from app.schemas.symptom import (
    SymptomBase,
    SymptomCreate,
    SymptomResponse,
)
from app.schemas.repair import (
    RepairHistoryBase,
    RepairHistoryCreate,
    RepairHistoryResponse,
)
from app.schemas.memory import (
    AgentMemoryBase,
    AgentMemoryCreate,
    AgentMemoryResponse,
)
from app.schemas.issue import (
    IssueBase,
    IssueCreate,
    IssueUpdate,
    IssueResponse,
)
from app.schemas.appliance import (
    ApplianceBase,
    ApplianceCreate,
    ApplianceUpdate,
    ApplianceResponse,
)

__all__ = [
    # Enums
    "ApplianceCategory",
    "IssueSeverity",
    "IssueStatus",
    "MemoryType",
    # Symptom
    "SymptomBase",
    "SymptomCreate",
    "SymptomResponse",
    # Repair History
    "RepairHistoryBase",
    "RepairHistoryCreate",
    "RepairHistoryResponse",
    # Agent Memory
    "AgentMemoryBase",
    "AgentMemoryCreate",
    "AgentMemoryResponse",
    # Issue Report
    "IssueBase",
    "IssueCreate",
    "IssueUpdate",
    "IssueResponse",
    # Appliance
    "ApplianceBase",
    "ApplianceCreate",
    "ApplianceUpdate",
    "ApplianceResponse",
]
