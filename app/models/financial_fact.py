from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class FinancialFact(Base):
    # A structured, time-aware financial data point about an Entity.
    #
    # Temporal semantics (do not infer business meaning beyond this):
    # - period_start/period_end represent a reporting or measurement period,
    #   appropriate for flow measures such as revenue or expenses over a
    #   quarter or year.
    # - as_of_date represents a single point-in-time observation, appropriate
    #   for stock/balance measures such as a share price or cash balance on
    #   a given date.
    # - A fact may populate period_start/period_end, only as_of_date, or in
    #   principle both - no single temporal pattern is enforced as
    #   mandatory. Absence of a field means no claim is made about that
    #   dimension, not that it is zero or unknown-but-implied.

    __tablename__ = "financial_facts"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    fact_type = Column(String, nullable=False, index=True)
    value_numeric = Column(Numeric(precision=20, scale=6), nullable=False)
    unit = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    as_of_date = Column(Date, nullable=True)
    source_id = Column(
        Integer, ForeignKey("research_sources.id"), nullable=True, index=True
    )
    created_at = Column(DateTime, server_default=func.now())

    source = relationship("ResearchSource")