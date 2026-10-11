from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class ResearchCase(Base):
    __tablename__ = "research_cases"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")

    # Point-in-time research boundary. NULL means no explicit cutoff was
    # set (the default for existing and casual/live research cases) - it
    # must never be silently defaulted to "now" at read time, since that
    # would claim a precision that was never actually asserted. Once set
    # at case creation, treat as immutable going forward (service-layer
    # convention for now, not yet DB-enforced). Used, once a consumer
    # exists, as: Facts/Events with published_at <= knowledge_cutoff_at
    # are "known" to this case; published_at IS NULL is excluded by
    # default from any point-in-time query, per the look-ahead-bias rule
    # established for FinancialFact/Event.
    knowledge_cutoff_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
