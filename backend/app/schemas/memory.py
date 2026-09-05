from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MemoryType


class AgentMemoryBase(BaseModel):
    memory_type: MemoryType = Field(..., description="Category of the agent memory")
    content: str = Field(..., description="Contextual memory content/insights")
    importance_score: float = Field(default=1.0, ge=0.0, le=10.0, description="Significance score (0.0 - 10.0)")


class AgentMemoryCreate(AgentMemoryBase):
    appliance_id: int = Field(..., description="ID of the appliance this memory relates to")


class AgentMemoryResponse(AgentMemoryBase):
    id: int
    appliance_id: int
    created_at: datetime
    last_confirmed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
