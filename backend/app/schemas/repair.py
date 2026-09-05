from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RepairHistoryBase(BaseModel):
    repair_type: str = Field(..., description="Type of repair performed (e.g. DIY, Professional Service)")
    description: Optional[str] = Field(None, description="Detailed repair description")
    parts_replaced: Optional[str] = Field(None, description="Names/part numbers of replaced components")
    service_cost: Optional[float] = Field(None, ge=0.0, description="Total service/parts cost (cannot be negative)")
    repair_date: Optional[date] = Field(None, description="Date the repair was carried out")
    outcome: Optional[str] = Field(None, description="Repair outcome (e.g. successful, temporary fix)")
    notes: Optional[str] = Field(None, description="Technician or user notes")


class RepairHistoryCreate(RepairHistoryBase):
    appliance_id: Optional[int] = Field(None, description="ID of the appliance repaired (can be inferred from path)")
    issue_id: Optional[int] = Field(None, description="Related issue report ID, if applicable")


class RepairHistoryResponse(RepairHistoryBase):
    id: int
    appliance_id: int
    issue_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
