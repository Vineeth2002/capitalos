from datetime import datetime, timezone

from pydantic import ValidationError

from app.data.connectors.registry import get_connector_class
from app.models.ingestion_run import IngestionRun
from app.models.source_record import SourceRecord
from app.schemas.financial_fact import FinancialFactCreate
from app.services import financial_fact_service
from app.services.financial_fact_service import FactReferenceError


class IngestionValidationError(Exception):
    pass


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _persist(db, canonical_facts, run_id):
    # Creates facts WITHOUT committing; the caller owns the transaction, so a
    # failure anywhere leaves no partial facts behind.
    created = []
    record_ids = {}

    for fact in canonical_facts:
        if not fact.fact_type:
            raise IngestionValidationError("Canonical fact is missing required fact_type")
        if fact.value_numeric is None:
            raise IngestionValidationError("Canonical fact is missing required value_numeric")

        source_record_id = None
        identifier = fact.source_record_identifier
        if run_id is not None and identifier is not None:
            if identifier not in record_ids:
                record = SourceRecord(ingestion_run_id=run_id, record_identifier=identifier)
                db.add(record)
                db.flush()
                record_ids[identifier] = record.id
            source_record_id = record_ids[identifier]

        try:
            fact_in = FinancialFactCreate(
                entity_id=fact.entity_id,
                security_id=fact.security_id,
                listing_id=fact.listing_id,
                fact_type=fact.fact_type,
                value_numeric=fact.value_numeric,
                unit=fact.unit,
                currency=fact.currency,
                period_start=fact.period_start,
                period_end=fact.period_end,
                as_of_date=fact.as_of_date,
                published_at=fact.published_at,
                source_id=fact.source_id,
                source_record_id=source_record_id,
            )
        except ValidationError as exc:
            raise IngestionValidationError("Invalid canonical fact: " + str(exc))

        try:
            created.append(financial_fact_service.create_fact(db, fact_in, commit=False))
        except FactReferenceError as exc:
            raise IngestionValidationError(exc.message)

    return created


def _finish_run(db, run_id, status):
    run = db.get(IngestionRun, run_id)
    run.status = status
    run.completed_at = _utcnow_naive()
    db.commit()


def ingest_from_provider(db, provider_name, raw_records):
    # Looks up a connector ONLY by name through the registry. One
    # IngestionRun is created per call and committed first, so it survives a
    # failed ingestion and is marked "failed".
    connector_class = get_connector_class(provider_name)

    run = IngestionRun(
        provider_name=provider_name,
        connector_version=getattr(connector_class, "connector_version", None),
        status="running",
        started_at=_utcnow_naive(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    run_id = run.id

    try:
        connector = connector_class(raw_records=raw_records)
        canonical_facts = connector.normalize(connector.fetch())
        created = _persist(db, canonical_facts, run_id)
        db.commit()
    except Exception:
        db.rollback()
        _finish_run(db, run_id, "failed")
        raise

    _finish_run(db, run_id, "completed")
    return created


def ingest_canonical_facts(db, canonical_facts):
    # Provider-agnostic persistence of already-canonical facts. No provider is
    # known here, so no IngestionRun or SourceRecord is created.
    try:
        created = _persist(db, canonical_facts, None)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return created