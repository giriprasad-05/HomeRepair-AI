from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Symptom(Base):
    __tablename__ = "symptoms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issue_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    issue: Mapped["IssueReport"] = relationship(
        "IssueReport",
        back_populates="symptoms"
    )

    __table_args__ = (
        Index("ix_symptoms_issue_name", "issue_id", "name"),
    )

    def __repr__(self) -> str:
        unit_str = f" {self.unit}" if self.unit else ""
        return f"<Symptom(id={self.id}, issue_id={self.issue_id}, name='{self.name}', value='{self.value}{unit_str}')>"
