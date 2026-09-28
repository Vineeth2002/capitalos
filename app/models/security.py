from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class Security(Base):
    # A tradeable instrument issued by an Entity of type "company".
    # Venue-specific identity (exchange + symbol) lives on Listing, not here.
    __tablename__ = "securities"
    __table_args__ = (
        UniqueConstraint("identifier_type", "identifier", name="uq_security_identifier"),
    )

    id = Column(Integer, primary_key=True, index=True)
    issuer_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    identifier_type = Column(String, nullable=True)
    identifier = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())