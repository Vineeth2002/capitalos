from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass(kw_only=True)
class CanonicalFinancialFact:
    """
    Provider-independent representation of one financial observation.

    Exactly one of entity_id / security_id / listing_id identifies the
    subject; connectors must supply already-resolved CapitalOS ids.
    Provider-specific identifiers must never appear here.

    source_record_identifier is the provider's id for the originating record.
    It is only honored when ingesting through ingest_from_provider(), which
    creates the IngestionRun the SourceRecord belongs to.

    All fields are keyword-only so new optional fields never break callers.
    """

    fact_type: str
    value_numeric: Decimal
    entity_id: Optional[int] = None
    security_id: Optional[int] = None
    listing_id: Optional[int] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    as_of_date: Optional[date] = None
    published_at: Optional[datetime] = None
    source_id: Optional[int] = None
    source_record_identifier: Optional[str] = None