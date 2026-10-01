from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ClassificationAppliesTo(str, Enum):
    financial_fact = "financial_fact"
    event = "event"


class FactClassificationCreate(BaseModel):
    applies_to: ClassificationAppliesTo
    type_name: str
    category: Optional[str] = None
    description: Optional[str] = None


class FactClassificationResponse(BaseModel):
    id: int
    applies_to: ClassificationAppliesTo
    type_name: str
    category: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True