from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class ClaimRelationship(Base):
    """
    A directed relationship between two Claims.

    This is a plain relational record, not a graph database primitive.
    The Reasoning Graph remains a computed view built from these rows,
    not a stored graph structure.
    """

    __tablename__ = "claim_relationships"

    id = Column(Integer, primary_key=True, index=True)

    from_claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    to_claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)

    relationship_type = Column(String, nullable=False)  # supports | contradicts | depends_on

    created_at = Column(DateTime, server_default=func.now())