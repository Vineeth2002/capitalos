from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class Listing(Base):
    # One venue-level listing of a Security (exchange + symbol).
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("security_id", "exchange", "symbol", name="uq_listing_venue_symbol"),
    )

    id = Column(Integer, primary_key=True, index=True)
    security_id = Column(Integer, ForeignKey("securities.id"), nullable=False, index=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())