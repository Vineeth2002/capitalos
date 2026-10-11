from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator

from app.schemas.financial_fact import FinancialFactResponse
from app.schemas.event import EventResponse


class ClaimEvidenceRelationshipType(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    context = "context"


class ClaimEvidenceCreate(BaseModel):
    financial_fact_id: Optional[int] = None
    event_id: Optional[int] = None
    relationship_type: ClaimEvidenceRelationshipType
    note: Optional[str] = None

    @model_validator(mode="after")
    def exactly_one_subject(self):
        supplied = [v for v in (self.financial_fact_id, self.event_id) if v is not None]
        if len(supplied) != 1:
            raise ValueError(
                "Exactly one of financial_fact_id, event_id must be provided"
            )
        return self


class ClaimEvidenceResponse(BaseModel):
    id: int
    claim_id: int
    financial_fact_id: Optional[int]
    event_id: Optional[int]
    relationship_type: ClaimEvidenceRelationshipType
    note: Optional[str]
    created_at: datetime
    financial_fact: Optional[FinancialFactResponse] = None
    event: Optional[EventResponse] = None

    class Config:
        from_attributes = True