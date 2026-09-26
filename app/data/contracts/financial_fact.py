from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class CanonicalFinancialFact:
    """
    Provider-independent representation of a single financial observation.

    This is the ONLY shape any connector may hand to the ingestion service.
    It contains exactly the fields the existing FinancialFact model needs
    and nothing else - no provider-specific identifiers, symbols, or
    timestamp formats. A connector's normalizer is responsible for mapping
    whatever the provider calls things into this shape; anything that
    cannot be mapped safely must be rejected by the connector rather than
    guessed here.
    """

    entity_id: int
    fact_type: str
    value_numeric: Decimal
    unit: Optional[str] = None
    currency: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    as_of_date: Optional[date] = None
    source_id: Optional[int] = None