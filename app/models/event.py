from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.sql import func

from app.db.base import Base


class Event(Base):
    # A discrete occurrence about exactly ONE subject: an Entity, a
    # Security, or a Listing. Distinct from FinancialFact (a numeric
    # observation) and Claim (a piece of reasoning) - an Event is neither;
    # it is something that happened.
    #
    # APPEND-ONLY, same discipline as FinancialFact: rows are never updated
    # after insertion. A correction is a NEW row whose supersedes_id points
    # back to the row it corrects.
    #
    # Time semantics (mirrors FinancialFact where the same distinction
    # applies):
    # - event_date: when the event occurred in the world (domain time).
    #   Nullable because an event's exact date is sometimes genuinely
    #   unknown or approximate when first recorded.
    # - published_at: when the event became publicly available/knowable.
    # - recorded_at: when CapitalOS wrote this row. NOT a look-ahead gate.

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN entity_id IS NULL THEN 0 ELSE 1 END "
            "+ CASE WHEN security_id IS NULL THEN 0 ELSE 1 END "
            "+ CASE WHEN listing_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="ck_event_exactly_one_subject",
        ),
        CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id",
            name="ck_event_no_self_supersession",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    security_id = Column(Integer, ForeignKey("securities.id"), nullable=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=True, index=True)

    event_type = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)

    event_date = Column(Date, nullable=True)
    published_at = Column(DateTime, nullable=True)

    source_id = Column(Integer, ForeignKey("research_sources.id"), nullable=True, index=True)
    source_record_id = Column(Integer, ForeignKey("source_records.id"), nullable=True, index=True)

    supersedes_id = Column(Integer, ForeignKey("events.id"), nullable=True, unique=True)
    supersession_reason = Column(String, nullable=True)

    recorded_at = Column(DateTime, server_default=func.now())