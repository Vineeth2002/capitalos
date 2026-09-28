from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.data.connectors.base import FinancialDataConnector
from app.data.connectors.registry import register_connector
from app.data.contracts.financial_fact import CanonicalFinancialFact
from app.data.ingestion.service import ingest_from_provider, IngestionValidationError
from app.models.financial_fact import FinancialFact
from app.models.ingestion_run import IngestionRun
from app.models.source_record import SourceRecord


def make_entity(client, name="Fact Co"):
    return client.post(
        "/entities",
        json={
            "entity_type": "company",
            "canonical_name": name,
            "ticker": None,
            "exchange": None,
            "status": "active",
        },
    ).json()["id"]


def make_security(client, issuer_id, identifier="INE111A01011"):
    return client.post(
        "/securities",
        json={"issuer_entity_id": issuer_id, "identifier_type": "ISIN", "identifier": identifier},
    ).json()["id"]


def make_listing(client, security_id, exchange="NSE", symbol="FCO"):
    return client.post(
        "/listings",
        json={"security_id": security_id, "exchange": exchange, "symbol": symbol},
    ).json()["id"]


def post_fact(client, **overrides):
    payload = {"fact_type": "revenue", "value_numeric": "100"}
    payload.update(overrides)
    return client.post("/financial-facts", json=payload)


# ---- subject integrity ----

def test_entity_only_subject_valid(client):
    entity_id = make_entity(client)
    response = post_fact(client, entity_id=entity_id)
    assert response.status_code == 201
    assert response.json()["entity_id"] == entity_id


def test_security_only_subject_valid(client):
    security_id = make_security(client, make_entity(client))
    response = post_fact(client, security_id=security_id, fact_type="shares_outstanding")
    assert response.status_code == 201
    assert response.json()["security_id"] == security_id


def test_listing_only_subject_valid(client):
    listing_id = make_listing(client, make_security(client, make_entity(client)))
    response = post_fact(client, listing_id=listing_id, fact_type="close_price")
    assert response.status_code == 201
    assert response.json()["listing_id"] == listing_id


def test_zero_subjects_rejected(client):
    assert post_fact(client).status_code == 422


def test_two_subjects_rejected(client):
    entity_id = make_entity(client)
    security_id = make_security(client, entity_id)
    assert post_fact(client, entity_id=entity_id, security_id=security_id).status_code == 422


def test_three_subjects_rejected(client):
    entity_id = make_entity(client)
    security_id = make_security(client, entity_id)
    listing_id = make_listing(client, security_id)
    response = post_fact(
        client, entity_id=entity_id, security_id=security_id, listing_id=listing_id
    )
    assert response.status_code == 422


def test_nonexistent_security_and_listing_rejected(client):
    assert post_fact(client, security_id=999999).status_code == 404
    assert post_fact(client, listing_id=999999).status_code == 404


def test_database_check_rejects_zero_two_and_three_subjects(client, db_session):
    entity_id = make_entity(client)
    security_id = make_security(client, entity_id)
    listing_id = make_listing(client, security_id)

    bad_rows = [
        FinancialFact(fact_type="x", value_numeric=Decimal("1")),
        FinancialFact(
            fact_type="x", value_numeric=Decimal("1"), entity_id=entity_id, security_id=security_id
        ),
        FinancialFact(
            fact_type="x",
            value_numeric=Decimal("1"),
            entity_id=entity_id,
            security_id=security_id,
            listing_id=listing_id,
        ),
    ]
    for row in bad_rows:
        db_session.add(row)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


def test_filters_by_security_and_listing(client):
    entity_id = make_entity(client)
    security_id = make_security(client, entity_id)
    listing_id = make_listing(client, security_id)
    post_fact(client, security_id=security_id, fact_type="shares_outstanding")
    post_fact(client, listing_id=listing_id, fact_type="close_price")

    by_security = client.get("/financial-facts", params={"security_id": security_id}).json()
    by_listing = client.get("/financial-facts", params={"listing_id": listing_id}).json()
    assert len(by_security) == 1
    assert len(by_listing) == 1


# ---- time ----

def test_published_at_and_recorded_at_persist(client):
    entity_id = make_entity(client)
    data = post_fact(client, entity_id=entity_id, published_at="2025-05-01T09:30:00").json()
    assert data["published_at"] == "2025-05-01T09:30:00"
    assert data["recorded_at"] is not None


def test_aware_published_at_is_stored_as_naive_utc(client):
    entity_id = make_entity(client)
    data = post_fact(
        client, entity_id=entity_id, published_at="2025-01-01T10:00:00+05:30"
    ).json()
    assert data["published_at"] == "2025-01-01T04:30:00"


def test_published_at_is_optional(client):
    entity_id = make_entity(client)
    assert post_fact(client, entity_id=entity_id).json()["published_at"] is None


# ---- supersession ----

def test_valid_correction_leaves_old_row_unchanged(client):
    entity_id = make_entity(client)
    original = post_fact(client, entity_id=entity_id, value_numeric="100").json()
    before = client.get(f"/financial-facts/{original['id']}").json()

    correction = post_fact(
        client,
        entity_id=entity_id,
        value_numeric="110",
        supersedes_id=original["id"],
        supersession_reason="provider restatement",
    )
    assert correction.status_code == 201
    assert correction.json()["supersedes_id"] == original["id"]
    assert correction.json()["supersession_reason"] == "provider restatement"

    after = client.get(f"/financial-facts/{original['id']}").json()
    assert after == before
    assert after["supersedes_id"] is None


def test_supersede_nonexistent_target_rejected(client):
    entity_id = make_entity(client)
    assert post_fact(client, entity_id=entity_id, supersedes_id=999999).status_code == 404


def test_supersede_subject_mismatch_rejected(client):
    entity_a = make_entity(client, "A Co")
    entity_b = make_entity(client, "B Co")
    original = post_fact(client, entity_id=entity_a).json()
    response = post_fact(client, entity_id=entity_b, supersedes_id=original["id"])
    assert response.status_code == 422


def test_supersede_fact_type_mismatch_rejected(client):
    entity_id = make_entity(client)
    original = post_fact(client, entity_id=entity_id, fact_type="revenue").json()
    response = post_fact(
        client, entity_id=entity_id, fact_type="net_income", supersedes_id=original["id"]
    )
    assert response.status_code == 422


def test_already_superseded_target_rejected(client):
    entity_id = make_entity(client)
    original = post_fact(client, entity_id=entity_id).json()
    assert post_fact(client, entity_id=entity_id, supersedes_id=original["id"]).status_code == 201
    assert post_fact(client, entity_id=entity_id, supersedes_id=original["id"]).status_code == 409


def test_database_rejects_self_supersession(client, db_session):
    entity_id = make_entity(client)
    fact = FinancialFact(fact_type="x", value_numeric=Decimal("1"), entity_id=entity_id)
    db_session.add(fact)
    db_session.commit()
    fact.supersedes_id = fact.id
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_enforces_unique_supersedes_id(client, db_session):
    entity_id = make_entity(client)
    original = FinancialFact(fact_type="x", value_numeric=Decimal("1"), entity_id=entity_id)
    db_session.add(original)
    db_session.commit()
    db_session.add(
        FinancialFact(
            fact_type="x", value_numeric=Decimal("2"), entity_id=entity_id, supersedes_id=original.id
        )
    )
    db_session.commit()
    db_session.add(
        FinancialFact(
            fact_type="x", value_numeric=Decimal("3"), entity_id=entity_id, supersedes_id=original.id
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---- provenance ----

def test_source_record_id_can_be_supplied_and_is_validated(client, db_session):
    entity_id = make_entity(client)
    assert post_fact(client, entity_id=entity_id, source_record_id=999999).status_code == 404

    run = IngestionRun(
        provider_name="manual_test",
        status="completed",
        started_at=datetime(2025, 1, 1),
    )
    db_session.add(run)
    db_session.commit()
    record = SourceRecord(ingestion_run_id=run.id, record_identifier="rec-1")
    db_session.add(record)
    db_session.commit()

    response = post_fact(client, entity_id=entity_id, source_record_id=record.id)
    assert response.status_code == 201
    assert response.json()["source_record_id"] == record.id


def test_source_record_unique_per_run(client, db_session):
    run = IngestionRun(
        provider_name="manual_test", status="completed", started_at=datetime(2025, 1, 1)
    )
    db_session.add(run)
    db_session.commit()
    db_session.add(SourceRecord(ingestion_run_id=run.id, record_identifier="dup"))
    db_session.commit()
    db_session.add(SourceRecord(ingestion_run_id=run.id, record_identifier="dup"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


class ProvenanceTestConnector(FinancialDataConnector):
    provider_name = "test_provenance_provider"
    connector_version = "1.2.3"

    def __init__(self, raw_records=None):
        self._raw = raw_records if raw_records is not None else []

    def fetch(self):
        return self._raw

    def normalize(self, raw_records):
        return [
            CanonicalFinancialFact(
                entity_id=r["entity"],
                fact_type=r.get("fact_type", "revenue"),
                value_numeric=Decimal(str(r["value"])),
                published_at=r.get("published_at"),
                source_record_identifier=r.get("rid"),
            )
            for r in raw_records
        ]


def test_ingestion_creates_run_and_reuses_source_records(client, db_session):
    register_connector(ProvenanceTestConnector.provider_name, ProvenanceTestConnector)
    entity_id = make_entity(client)
    raw = [
        {"entity": entity_id, "value": 1, "rid": "rec-A"},
        {"entity": entity_id, "value": 2, "rid": "rec-A", "fact_type": "net_income"},
        {"entity": entity_id, "value": 3, "rid": "rec-B", "fact_type": "ebitda"},
    ]

    created = ingest_from_provider(db_session, "test_provenance_provider", raw)
    assert len(created) == 3

    runs = db_session.query(IngestionRun).filter_by(provider_name="test_provenance_provider").all()
    assert len(runs) == 1
    assert runs[0].connector_version == "1.2.3"
    assert runs[0].status == "completed"
    assert runs[0].completed_at is not None

    records = db_session.query(SourceRecord).filter_by(ingestion_run_id=runs[0].id).all()
    assert sorted(r.record_identifier for r in records) == ["rec-A", "rec-B"]

    assert created[0].source_record_id == created[1].source_record_id
    assert created[0].source_record_id != created[2].source_record_id


def test_ingestion_without_record_identifier_creates_no_source_record(client, db_session):
    register_connector(ProvenanceTestConnector.provider_name, ProvenanceTestConnector)
    entity_id = make_entity(client)
    created = ingest_from_provider(
        db_session, "test_provenance_provider", [{"entity": entity_id, "value": 5}]
    )
    assert created[0].source_record_id is None
    assert db_session.query(SourceRecord).count() == 0
    assert db_session.query(IngestionRun).count() == 1


def test_ingestion_persists_published_at_as_naive_utc(client, db_session):
    register_connector(ProvenanceTestConnector.provider_name, ProvenanceTestConnector)
    entity_id = make_entity(client)
    aware = datetime(2025, 1, 1, 10, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    created = ingest_from_provider(
        db_session,
        "test_provenance_provider",
        [{"entity": entity_id, "value": 5, "published_at": aware}],
    )
    assert created[0].published_at == datetime(2025, 1, 1, 4, 30)


def test_failed_ingestion_marks_run_failed_and_keeps_no_facts(client, db_session):
    register_connector(ProvenanceTestConnector.provider_name, ProvenanceTestConnector)
    entity_id = make_entity(client)
    raw = [
        {"entity": entity_id, "value": 1, "rid": "good"},
        {"entity": 999999, "value": 2, "rid": "bad"},
    ]

    with pytest.raises(IngestionValidationError):
        ingest_from_provider(db_session, "test_provenance_provider", raw)

    runs = db_session.query(IngestionRun).filter_by(provider_name="test_provenance_provider").all()
    assert len(runs) == 1
    assert runs[0].status == "failed"
    assert db_session.query(FinancialFact).count() == 0
    assert db_session.query(SourceRecord).count() == 0


def test_unknown_provider_creates_no_run(db_session):
    with pytest.raises(KeyError):
        ingest_from_provider(db_session, "provider_that_does_not_exist", [])
    assert db_session.query(IngestionRun).count() == 0