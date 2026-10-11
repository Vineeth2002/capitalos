from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ResearchCaseCreate(BaseModel):
    entity_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str = "active"
    knowledge_cutoff_at: Optional[datetime] = None


class ResearchCaseUpdate(BaseModel):
    entity_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    knowledge_cutoff_at: Optional[datetime] = None


class ResearchCaseResponse(BaseModel):
    id: int
    entity_id: Optional[int]
    title: str
    description: Optional[str]
    status: str
    knowledge_cutoff_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
