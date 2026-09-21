from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.schemas.research_source import ResearchSourceResponse


class ClaimSourceRelationshipType(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    context = "context"


class ClaimSourceCreate(BaseModel):
    source_id: int
    relationship_type: ClaimSourceRelationshipType
    excerpt: Optional[str] = None


class ClaimSourceResponse(BaseModel):
    id: int
    claim_id: int
    source_id: int
    relationship_type: ClaimSourceRelationshipType
    excerpt: Optional[str]
    created_at: datetime
    source: ResearchSourceResponse

    class Config:
        from_attributes = True