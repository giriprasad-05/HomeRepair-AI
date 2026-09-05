from datetime import date
from typing import Optional
from sqlalchemy import String, Text, Float, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RepairHistory(Base):
    __tablename__ = "repair_histories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    appliance_id: Mapped[int] = mapped_column(
        ForeignKey("appliances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    issue_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("issue_reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    repair_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parts_replaced: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    service_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    repair_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    appliance: Mapped["Appliance"] = relationship(
        "Appliance",
        back_populates="repairs"
    )
    issue: Mapped[Optional["IssueReport"]] = relationship(
        "IssueReport",
        back_populates="repairs"
    )

    __table_args__ = (
        Index("ix_repair_histories_appliance_date", "appliance_id", "repair_date"),
    )

    def __repr__(self) -> str:
        return f"<RepairHistory(id={self.id}, appliance_id={self.appliance_id}, type='{self.repair_type}', date={self.repair_date})>"
