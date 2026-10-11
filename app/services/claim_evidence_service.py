from sqlalchemy.exc import IntegrityError

from app.models.claim import Claim
from app.models.claim_evidence import ClaimEvidence
from app.models.event import Event
from app.models.financial_fact import FinancialFact

_DUPLICATE_EVIDENCE_CONSTRAINTS = {"uq_claim_evidence_fact", "uq_claim_evidence_event"}


class ClaimEvidenceError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _violated_constraint_name(integrity_error):
    # Returns the Postgres constraint/index name that caused this
    # IntegrityError, or None if it cannot be determined. Uses the
    # underlying psycopg driver exception's diagnostics, which is the
    # precise, version-stable way to identify the failing constraint -
    # deliberately not string-matching the error message text, which can
    # vary by Postgres version or locale.
    orig = getattr(integrity_error, "orig", None)
    diag = getattr(orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def attach_evidence(db, claim_id, evidence_in):
    claim = db.get(Claim, claim_id)
    if not claim:
        raise ClaimEvidenceError(404, "Claim not found")

    if evidence_in.financial_fact_id is not None:
        fact = db.get(FinancialFact, evidence_in.financial_fact_id)
        if not fact:
            raise ClaimEvidenceError(404, "Financial fact not found")

    if evidence_in.event_id is not None:
        event = db.get(Event, evidence_in.event_id)
        if not event:
            raise ClaimEvidenceError(404, "Event not found")

    # Fast-path check: catches the common case and gives a clean error
    # without touching the database's own constraint machinery.
    existing = (
        db.query(ClaimEvidence)
        .filter(
            ClaimEvidence.claim_id == claim_id,
            ClaimEvidence.financial_fact_id == evidence_in.financial_fact_id,
            ClaimEvidence.event_id == evidence_in.event_id,
        )
        .first()
    )
    if existing:
        raise ClaimEvidenceError(
            409, "This evidence is already attached to this claim"
        )

    evidence = ClaimEvidence(
        claim_id=claim_id,
        financial_fact_id=evidence_in.financial_fact_id,
        event_id=evidence_in.event_id,
        relationship_type=evidence_in.relationship_type.value,
        note=evidence_in.note,
    )
    db.add(evidence)

    # Slow-path safety net: if a concurrent request inserted the same
    # pair between the check above and this commit, the database's own
    # partial unique index raises IntegrityError. Only THIS specific
    # pair of constraints is remapped to the 409 duplicate-evidence
    # error. Any other IntegrityError (e.g. a FK violation from a race
    # with a concurrent delete, or something unanticipated) is rolled
    # back and re-raised as-is, rather than being mislabeled as a
    # duplicate - precision here matters more than convenience, since
    # silently mislabeling an unrelated integrity failure as "duplicate
    # evidence" would hide a real bug behind a plausible-sounding error.
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        constraint_name = _violated_constraint_name(exc)
        if constraint_name in _DUPLICATE_EVIDENCE_CONSTRAINTS:
            raise ClaimEvidenceError(
                409, "This evidence is already attached to this claim"
            )
        raise

    db.refresh(evidence)
    return evidence


def list_evidence_for_claim(db, claim_id):
    return (
        db.query(ClaimEvidence)
        .filter(ClaimEvidence.claim_id == claim_id)
        .order_by(ClaimEvidence.created_at.asc())
        .all()
    )


def get_claim_evidence(db, claim_id, evidence_id):
    return (
        db.query(ClaimEvidence)
        .filter(ClaimEvidence.claim_id == claim_id, ClaimEvidence.id == evidence_id)
        .first()
    )


def detach_evidence(db, evidence):
    db.delete(evidence)
    db.commit()
