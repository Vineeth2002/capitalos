from typing import Optional

from pydantic import BaseModel


class ReasoningIntakeRequest(BaseModel):
    text: str


class DraftClaim(BaseModel):
    statement: str
    temporal_orientation: str
    epistemic_role: str
    shape: str


class InferredCandidate(BaseModel):
    statement: str
    reason: str


class ReasoningIntakeResponse(BaseModel):
    objective_context: Optional[str]
    draft_claims: list[DraftClaim]
    inferred_candidates: list[InferredCandidate]
    needs_more_reasoning: bool
    message: Optional[str]