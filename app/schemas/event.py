from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from app.schemas.research_source import ResearchSourceResponse


class EventCreate(BaseModel):
    # Exactly one of entity_id / security_id / listing_id must be supplied.
    entity_id: Optional[int] = None
    security_id: Optional[int] = None
    listing_id: Optional[int] = None
    event_type: str
    description: str
    event_date: Optional[date] = None
    published_at: Optional[datetime] = None
    source_id: Optional[int] = None
    source_record_id: Optional[int] = None
    supersedes_id: Optional[int] = None
    supersession_reason: Optional[str] = None

    @model_validator(mode="after")
    def exactly_one_subject(self):
        supplied = [
            v for v in (self.entity_id, self.security_id, self.listing_id) if v is not None
        ]
        if len(supplied) != 1:
            raise ValueError(
                "Exactly one of entity_id, security_id, listing_id must be provided"
            )
        return self


class EventResponse(BaseModel):
    id: int
    entity_id: Optional[int]
    security_id: Optional[int]
    listing_id: Optional[int]
    event_type: str
    description: str
    event_date: Optional[date]
    published_at: Optional[datetime]
    source_id: Optional[int]
    source_record_id: Optional[int]
    supersedes_id: Optional[int]
    supersession_reason: Optional[str]
    source: Optional[ResearchSourceResponse] = None
    recorded_at: datetime

    class Config:
        from_attributes = True