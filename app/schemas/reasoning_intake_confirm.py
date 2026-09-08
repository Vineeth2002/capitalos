from typing import Optional

from pydantic import BaseModel

from app.schemas.claim import ClaimResponse
from app.schemas.research_case import ResearchCaseResponse


class ConfirmedClaimInput(BaseModel):
    entity_id: Optional[int] = None
    statement: str
    temporal_orientation: str
    epistemic_role: str
    shape: str
    confidence_band: Optional[str] = None
    lifecycle_status: str = "active"
    lens: Optional[str] = None
    origin: str


class ReasoningIntakeConfirmRequest(BaseModel):
    entity_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    claims: list[ConfirmedClaimInput]


class ReasoningIntakeConfirmResponse(BaseModel):
    research_case: ResearchCaseResponse
    claims: list[ClaimResponse]