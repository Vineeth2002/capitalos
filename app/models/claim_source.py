from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ClaimSource(Base):
    __tablename__ = "claim_sources"
    __table_args__ = (
        UniqueConstraint("claim_id", "source_id", name="uq_claim_source"),
    )

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    source_id = Column(
        Integer, ForeignKey("research_sources.id"), nullable=False, index=True
    )
    relationship_type = Column(String, nullable=False)
    excerpt = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    source = relationship("ResearchSource")