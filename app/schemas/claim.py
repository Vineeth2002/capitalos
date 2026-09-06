from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel

TemporalOrientation = Literal["historical", "current", "forecast"]
EpistemicRole = Literal["evidence", "interpretation", "assumption", "risk", "hypothesis"]
Shape = Literal["quantitative", "qualitative"]
ConfidenceBand = Literal["low", "medium", "high"]
LifecycleStatus = Literal["active", "superseded", "invalidated", "expired"]
Lens = Literal["fundamental", "macro", "quant", "strategic", "risk", "behavioural"]
Origin = Literal["user", "ai_suggested", "engine_generated", "imported"]


class ClaimCreate(BaseModel):
    entity_id: Optional[int] = None
    statement: str
    temporal_orientation: TemporalOrientation
    epistemic_role: EpistemicRole
    shape: Shape
    confidence_band: Optional[ConfidenceBand] = None
    lifecycle_status: LifecycleStatus = "active"
    lens: Optional[Lens] = None
    origin: Origin


class ClaimUpdate(BaseModel):
    entity_id: Optional[int] = None
    statement: Optional[str] = None
    temporal_orientation: Optional[TemporalOrientation] = None
    epistemic_role: Optional[EpistemicRole] = None
    shape: Optional[Shape] = None
    confidence_band: Optional[ConfidenceBand] = None
    lifecycle_status: Optional[LifecycleStatus] = None
    lens: Optional[Lens] = None
    origin: Optional[Origin] = None


class ClaimResponse(BaseModel):
    id: int
    research_case_id: int
    entity_id: Optional[int] = None
    statement: str
    temporal_orientation: TemporalOrientation
    epistemic_role: EpistemicRole
    shape: Shape
    confidence_band: Optional[ConfidenceBand] = None
    lifecycle_status: LifecycleStatus
    lens: Optional[Lens] = None
    origin: Origin
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True