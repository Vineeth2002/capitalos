from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class FinancialFact(Base):
    # A structured, time-aware financial observation about exactly ONE subject:
    # an Entity, a Security, or a Listing.
    #
    # APPEND-ONLY: rows are never updated after insertion. A correction is a
    # NEW row whose supersedes_id points back to the row it corrects.
    #
    # observation_kind distinguishes observed (directly sourced), derived
    # (computed from other facts), and inferred (estimated/AI-produced)
    # values. No derivation lineage is stored yet - that is a future
    # Fact-to-Fact relationship, not a precondition for this distinction
    # to exist.
    #
    # Time semantics (timestamps are naive UTC, matching the rest of the schema):
    # - period_start/period_end: reporting or measurement period (flow measures).
    # - as_of_date: point-in-time observation date (stock measures such as price).
    # - published_at: when the information became publicly available.
    # - recorded_at: when CapitalOS wrote this row. NOT a look-ahead gate.
    # Absence of a field means no claim is made about that dimension.

    __tablename__ = "financial_facts"
    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN entity_id IS NULL THEN 0 ELSE 1 END "
            "+ CASE WHEN security_id IS NULL THEN 0 ELSE 1 END "
            "+ CASE WHEN listing_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="ck_financial_fact_exactly_one_subject",
        ),
        CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id",
            name="ck_financial_fact_no_self_supersession",
        ),
        CheckConstraint(
            "observation_kind IN ('observed', 'derived', 'inferred')",
            name="ck_financial_fact_observation_kind",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    security_id = Column(Integer, ForeignKey("securities.id"), nullable=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=True, index=True)

    fact_type = Column(String, nullable=False, index=True)
    value_numeric = Column(Numeric(precision=20, scale=6), nullable=False)
    unit = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    observation_kind = Column(String, nullable=False, server_default="observed")

    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    as_of_date = Column(Date, nullable=True)
    published_at = Column(DateTime, nullable=True)

    source_id = Column(Integer, ForeignKey("research_sources.id"), nullable=True, index=True)
    source_record_id = Column(Integer, ForeignKey("source_records.id"), nullable=True, index=True)

    supersedes_id = Column(Integer, ForeignKey("financial_facts.id"), nullable=True, unique=True)
    supersession_reason = Column(String, nullable=True)

    recorded_at = Column(DateTime, server_default=func.now())

    source = relationship("ResearchSource")