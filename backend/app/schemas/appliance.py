from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ApplianceCategory
from app.schemas.issue import IssueResponse
from app.schemas.repair import RepairHistoryResponse
from app.schemas.memory import AgentMemoryResponse


class ApplianceBase(BaseModel):
    name: str = Field(..., description="Name or nickname for the appliance")
    brand: Optional[str] = Field(None, description="Manufacturer brand name")
    model_number: Optional[str] = Field(None, description="Appliance model number")
    category: ApplianceCategory = Field(..., description="Appliance category")
    purchase_date: Optional[date] = Field(None, description="Date of purchase")
    warranty_expiry: Optional[date] = Field(None, description="Date warranty expires")
    location: Optional[str] = Field(None, description="Location in home (e.g. Kitchen, Basement)")
    notes: Optional[str] = Field(None, description="General user notes")
    is_active: bool = Field(default=True, description="Whether the appliance is actively in use")


class ApplianceCreate(ApplianceBase):
    @model_validator(mode="after")
    def validate_dates(self):
        if self.purchase_date and self.purchase_date > date.today():
            raise ValueError("purchase_date cannot be in the future")
        if self.purchase_date and self.warranty_expiry and self.warranty_expiry < self.purchase_date:
            raise ValueError("warranty_expiry cannot be earlier than purchase_date")
        return self


class ApplianceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name or nickname for the appliance")
    brand: Optional[str] = Field(None, description="Manufacturer brand name")
    model_number: Optional[str] = Field(None, description="Appliance model number")
    category: Optional[ApplianceCategory] = Field(None, description="Appliance category")
    purchase_date: Optional[date] = Field(None, description="Date of purchase")
    warranty_expiry: Optional[date] = Field(None, description="Date warranty expires")
    location: Optional[str] = Field(None, description="Location in home")
    notes: Optional[str] = Field(None, description="General user notes")
    is_active: Optional[bool] = Field(None, description="Whether the appliance is actively in use")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.purchase_date and self.purchase_date > date.today():
            raise ValueError("purchase_date cannot be in the future")
        if self.purchase_date and self.warranty_expiry and self.warranty_expiry < self.purchase_date:
            raise ValueError("warranty_expiry cannot be earlier than purchase_date")
        return self


class ApplianceResponse(ApplianceBase):
    id: int
    created_at: datetime
    issues: List[IssueResponse] = []
    repairs: List[RepairHistoryResponse] = []
    memories: List[AgentMemoryResponse] = []

    model_config = ConfigDict(from_attributes=True)
