from datetime import timezone

from app.models.entity import Entity
from app.models.financial_fact import FinancialFact
from app.models.listing import Listing
from app.models.research_source import ResearchSource
from app.models.security import Security
from app.models.source_record import SourceRecord


class FactReferenceError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _naive_utc(value):
    # The schema stores naive UTC datetimes. Aware inputs are converted to UTC
    # and stripped; naive inputs are taken as already UTC.
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def validate_references(db, fact_in):
    if fact_in.entity_id is not None and not db.get(Entity, fact_in.entity_id):
        raise FactReferenceError(404, "Entity not found")
    if fact_in.security_id is not None and not db.get(Security, fact_in.security_id):
        raise FactReferenceError(404, "Security not found")
    if fact_in.listing_id is not None and not db.get(Listing, fact_in.listing_id):
        raise FactReferenceError(404, "Listing not found")
    if fact_in.source_id is not None and not db.get(ResearchSource, fact_in.source_id):
        raise FactReferenceError(404, "Source not found")
    if fact_in.source_record_id is not None and not db.get(
        SourceRecord, fact_in.source_record_id
    ):
        raise FactReferenceError(404, "Source record not found")

    if fact_in.supersedes_id is not None:
        target = db.get(FinancialFact, fact_in.supersedes_id)
        if not target:
            raise FactReferenceError(404, "Fact to supersede not found")
        target_subject = (target.entity_id, target.security_id, target.listing_id)
        new_subject = (fact_in.entity_id, fact_in.security_id, fact_in.listing_id)
        if target_subject != new_subject:
            raise FactReferenceError(422, "A correction must have the same subject")
        if target.fact_type != fact_in.fact_type:
            raise FactReferenceError(422, "A correction must have the same fact_type")
        already = (
            db.query(FinancialFact)
            .filter(FinancialFact.supersedes_id == target.id)
            .first()
        )
        if already:
            raise FactReferenceError(409, "This fact has already been superseded")


def create_fact(db, fact_in, commit=True):
    validate_references(db, fact_in)

    fact = FinancialFact(
        entity_id=fact_in.entity_id,
        security_id=fact_in.security_id,
        listing_id=fact_in.listing_id,
        fact_type=fact_in.fact_type,
        value_numeric=fact_in.value_numeric,
        unit=fact_in.unit,
        currency=fact_in.currency,
        observation_kind=fact_in.observation_kind.value,
        period_start=fact_in.period_start,
        period_end=fact_in.period_end,
        as_of_date=fact_in.as_of_date,
        published_at=_naive_utc(fact_in.published_at),
        source_id=fact_in.source_id,
        source_record_id=fact_in.source_record_id,
        supersedes_id=fact_in.supersedes_id,
        supersession_reason=fact_in.supersession_reason,
    )
    db.add(fact)
    if commit:
        db.commit()
        db.refresh(fact)
    else:
        db.flush()
    return fact


def get_fact(db, fact_id):
    return db.get(FinancialFact, fact_id)


def list_facts(db, entity_id=None, security_id=None, listing_id=None, fact_type=None):
    query = db.query(FinancialFact)
    if entity_id is not None:
        query = query.filter(FinancialFact.entity_id == entity_id)
    if security_id is not None:
        query = query.filter(FinancialFact.security_id == security_id)
    if listing_id is not None:
        query = query.filter(FinancialFact.listing_id == listing_id)
    if fact_type is not None:
        query = query.filter(FinancialFact.fact_type == fact_type)
    return query.order_by(FinancialFact.id.asc()).all()