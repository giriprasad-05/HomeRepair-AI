from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SymptomBase(BaseModel):
    name: str = Field(..., description="Name of the symptom (e.g. temperature, vibration, error_code)")
    value: str = Field(..., description="Observed symptom value (e.g. 42, grinding)")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g. celsius, dB)")


class SymptomCreate(SymptomBase):
    issue_id: Optional[int] = Field(None, description="ID of the related issue report")


class SymptomResponse(SymptomBase):
    id: int
    issue_id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
