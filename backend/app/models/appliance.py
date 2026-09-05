from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Date, DateTime, Enum as SQLEnum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ApplianceCategory


class Appliance(Base):
    __tablename__ = "appliances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    model_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[ApplianceCategory] = mapped_column(
        SQLEnum(ApplianceCategory, name="appliance_category_enum", native_enum=False),
        nullable=False,
        index=True
    )
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    warranty_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    issues: Mapped[List["IssueReport"]] = relationship(
        "IssueReport",
        back_populates="appliance",
        cascade="all, delete-orphan"
    )
    repairs: Mapped[List["RepairHistory"]] = relationship(
        "RepairHistory",
        back_populates="appliance",
        cascade="all, delete-orphan"
    )
    memories: Mapped[List["AgentMemory"]] = relationship(
        "AgentMemory",
        back_populates="appliance",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_appliances_brand_model", "brand", "model_number"),
        Index("ix_appliances_category_active", "category", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Appliance(id={self.id}, name='{self.name}', brand='{self.brand}', model='{self.model_number}')>"
