from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SourceType(str, Enum):
    filing = "filing"
    regulator = "regulator"
    annual_report = "annual_report"
    company = "company"
    research = "research"
    news = "news"
    dataset = "dataset"
    other = "other"


class ResearchSourceCreate(BaseModel):
    title: str
    url: Optional[str] = None
    publisher: Optional[str] = None
    source_type: SourceType
    published_at: Optional[datetime] = None
    accessed_at: Optional[datetime] = None


class ResearchSourceResponse(BaseModel):
    id: int
    title: str
    url: Optional[str]
    publisher: Optional[str]
    source_type: SourceType
    published_at: Optional[datetime]
    accessed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True