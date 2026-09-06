from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class RelationshipType(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    depends_on = "depends_on"


class ClaimRelationshipCreate(BaseModel):
    to_claim_id: int
    relationship_type: RelationshipType


class ClaimRelationshipResponse(BaseModel):
    id: int
    from_claim_id: int
    to_claim_id: int
    relationship_type: RelationshipType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)