from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.schemas.research_source import ResearchSourceResponse


class FinancialFactCreate(BaseModel):
    entity_id: int
    fact_type: str
    value_numeric: Decimal
    unit: Optional[str] = None
    currency: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    as_of_date: Optional[date] = None
    source_id: Optional[int] = None


class FinancialFactResponse(BaseModel):
    id: int
    entity_id: int
    fact_type: str
    value_numeric: Decimal
    unit: Optional[str]
    currency: Optional[str]
    period_start: Optional[date]
    period_end: Optional[date]
    as_of_date: Optional[date]
    source_id: Optional[int]
    source: Optional[ResearchSourceResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True