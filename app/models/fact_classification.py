from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class FactClassification(Base):
    # An advisory registry mapping a known fact_type or event_type string
    # to a category. This does NOT constrain FinancialFact.fact_type or
    # Event.event_type at the database level - both remain free strings,
    # exactly as in Phase 11B/12/13, so existing and future rows using an
    # unregistered type string are unaffected. A type_name with no
    # matching row here is simply unclassified, not invalid.
    __tablename__ = "fact_classifications"
    __table_args__ = (
        UniqueConstraint("applies_to", "type_name", name="uq_fact_classification_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    applies_to = Column(String, nullable=False)  # "financial_fact" | "event"
    type_name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())