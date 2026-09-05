from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import IssueSeverity, IssueStatus


class IssueReport(Base):
    __tablename__ = "issue_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    appliance_id: Mapped[int] = mapped_column(
        ForeignKey("appliances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[IssueSeverity] = mapped_column(
        SQLEnum(IssueSeverity, name="issue_severity_enum", native_enum=False),
        default=IssueSeverity.MEDIUM,
        nullable=False,
        index=True
    )
    status: Mapped[IssueStatus] = mapped_column(
        SQLEnum(IssueStatus, name="issue_status_enum", native_enum=False),
        default=IssueStatus.OPEN,
        nullable=False,
        index=True
    )
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    appliance: Mapped["Appliance"] = relationship(
        "Appliance",
        back_populates="issues"
    )
    symptoms: Mapped[List["Symptom"]] = relationship(
        "Symptom",
        back_populates="issue",
        cascade="all, delete-orphan"
    )
    repairs: Mapped[List["RepairHistory"]] = relationship(
        "RepairHistory",
        back_populates="issue"
    )

    __table_args__ = (
        Index("ix_issue_reports_appliance_status", "appliance_id", "status"),
        Index("ix_issue_reports_status_severity", "status", "severity"),
    )

    def __repr__(self) -> str:
        return f"<IssueReport(id={self.id}, appliance_id={self.appliance_id}, title='{self.title}', status='{self.status}')>"
