from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ClaimEvidence(Base):
    # Links a Claim to exactly ONE structured observation: a FinancialFact
    # OR an Event (never both, never neither). This is the bridge between
    # the Financial World layer (FinancialFact/Event) and the Reasoning
    # layer (Claim) - distinct from ClaimSource, which links a Claim to a
    # human-facing ResearchSource (a document citation), not to structured
    # data.
    #
    # This table deliberately does NOT represent "assessment" or "current
    # knowledge state" - it only records that a claim cites a specific
    # fact or event, and how (supports/contradicts/context). Whether that
    # evidence is still current, disputed, or superseded is computed at
    # query time from the referenced FinancialFact/Event's own fields
    # (supersedes_id, published_at), never stored here.
    #
    # DUPLICATE PREVENTION: a plain multi-column UNIQUE constraint across
    # (claim_id, financial_fact_id, event_id) would NOT work here, because
    # Postgres treats every NULL as distinct from every other NULL - so a
    # three-column unique constraint with two routinely-null columns gives
    # no real protection. Instead, two separate PARTIAL unique indexes
    # enforce the actual invariant: a claim can reference the same fact at
    # most once, and the same event at most once, independently of each
    # other - while leaving financial_fact_id/event_id free to repeat
    # across DIFFERENT claims (the same fact/event can support many
    # claims).

    __tablename__ = "claim_evidence"
    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN financial_fact_id IS NULL THEN 0 ELSE 1 END "
            "+ CASE WHEN event_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="ck_claim_evidence_exactly_one_subject",
        ),
        Index(
            "uq_claim_evidence_fact",
            "claim_id",
            "financial_fact_id",
            unique=True,
            postgresql_where=(Column("financial_fact_id") != None),  # noqa: E711
        ),
        Index(
            "uq_claim_evidence_event",
            "claim_id",
            "event_id",
            unique=True,
            postgresql_where=(Column("event_id") != None),  # noqa: E711
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    financial_fact_id = Column(
        Integer, ForeignKey("financial_facts.id"), nullable=True, index=True
    )
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)

    relationship_type = Column(String, nullable=False)  # supports | contradicts | context
    note = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    financial_fact = relationship("FinancialFact")
    event = relationship("Event")
