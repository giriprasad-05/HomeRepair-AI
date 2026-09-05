from datetime import datetime
from typing import Optional
from sqlalchemy import Text, Float, DateTime, ForeignKey, Enum as SQLEnum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import MemoryType


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    appliance_id: Mapped[int] = mapped_column(
        ForeignKey("appliances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        SQLEnum(MemoryType, name="memory_type_enum", native_enum=False),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    appliance: Mapped["Appliance"] = relationship(
        "Appliance",
        back_populates="memories"
    )

    __table_args__ = (
        Index("ix_agent_memories_appliance_type", "appliance_id", "memory_type"),
        Index("ix_agent_memories_importance", "importance_score"),
    )

    def __repr__(self) -> str:
        return f"<AgentMemory(id={self.id}, appliance_id={self.appliance_id}, type='{self.memory_type}', importance={self.importance_score})>"
