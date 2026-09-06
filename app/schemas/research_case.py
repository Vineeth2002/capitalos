from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel

ResearchCaseStatus = Literal["active", "archived"]


class ResearchCaseCreate(BaseModel):
    entity_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: ResearchCaseStatus = "active"


class ResearchCaseUpdate(BaseModel):
    entity_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ResearchCaseStatus] = None


class ResearchCaseResponse(BaseModel):
    id: int
    entity_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: ResearchCaseStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True