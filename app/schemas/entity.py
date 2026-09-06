from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel

EntityType = Literal["company", "person", "sector", "country", "asset", "other"]
EntityStatus = Literal["active", "inactive"]


class EntityCreate(BaseModel):
    entity_type: EntityType
    canonical_name: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    status: EntityStatus = "active"


class EntityUpdate(BaseModel):
    entity_type: Optional[EntityType] = None
    canonical_name: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    status: Optional[EntityStatus] = None


class EntityResponse(BaseModel):
    id: int
    entity_type: EntityType
    canonical_name: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    status: EntityStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True