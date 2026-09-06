from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ChallengeCategory(str, Enum):
    missing_evidence = "missing_evidence"
    unstated_assumption = "unstated_assumption"
    contradiction = "contradiction"
    alternative_explanation = "alternative_explanation"
    invalidation_condition = "invalidation_condition"


class ChallengeOutputResponse(BaseModel):
    id: int
    research_case_id: int
    category: ChallengeCategory
    text: str
    claim_ids: list[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)