from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IssueSeverity, IssueStatus
from app.schemas.symptom import SymptomCreate, SymptomResponse


class IssueBase(BaseModel):
    title: str = Field(..., description="Summary of the problem")
    description: Optional[str] = Field(None, description="Detailed problem description")
    severity: IssueSeverity = Field(default=IssueSeverity.MEDIUM, description="Issue severity level")
    status: IssueStatus = Field(default=IssueStatus.OPEN, description="Current workflow status")


class IssueCreate(IssueBase):
    appliance_id: Optional[int] = Field(default=None, description="ID of the appliance experiencing the issue (can be inferred from path)")
    symptoms: Optional[List[SymptomCreate]] = Field(default=None, description="Initial symptoms observed")


class IssueUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Summary of the problem")
    description: Optional[str] = Field(None, description="Detailed problem description")
    severity: Optional[IssueSeverity] = Field(None, description="Issue severity level")
    status: Optional[IssueStatus] = Field(None, description="Current workflow status")
    resolved_at: Optional[datetime] = Field(None, description="Timestamp when resolved")


class IssueResponse(IssueBase):
    id: int
    appliance_id: int
    reported_at: datetime
    resolved_at: Optional[datetime] = None
    symptoms: List[SymptomResponse] = []

    model_config = ConfigDict(from_attributes=True)
