from decimal import Decimal

from app.data.connectors.mock_provider_a import MockProviderAConnector
from app.data.connectors.mock_provider_b import MockProviderBConnector
from app.data.ingestion.service import ingest_canonical_facts, IngestionValidationError


def create_entity(client, **overrides):
    payload = {
        "entity_type": "company",
        "canonical_name": "Connector Test Corp",
        "ticker": "CTC",
        "exchange": "NASDAQ",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/entities", json=payload)


def create_source(client, **overrides):
    payload = {
        "title": "Connector Test Source",
        "url": "https://example.com",
        "publisher": "Test Publisher",
        "source_type": "filing",
    }
    payload.update(overrides)
    return client.post("/research-sources", json=payload)


def test_provider_a_normalizes_to_canonical_shape(client):
    entity_id = create_entity(client).json()["id"]
    source_id = create_source(client).json()["id"]

    raw = [
        {
            "company_id": entity_id,
            "revenue": Decimal("1000000"),
            "period_start": "2025-01-01",
            "period_end": "2025-03-31",
            "currency_code": "USD",
            "source_ref": source_id,
        }
    ]
    connector = MockProviderAConnector(raw_records=raw)
    canonical = connector.normalize(connector.fetch())

    assert len(canonical) == 1
    fact = canonical[0]
    assert fact.entity_id == entity_id
    assert fact.fact_type == "revenue"
    assert fact.value_numeric == Decimal("1000000")
    assert fact.currency == "USD"
    assert fact.source_id == source_id


def test_provider_b_normalizes_to_canonical_shape(client):
    entity_id = create_entity(client).json()["id"]
    source_id = create_source(client).json()["id"]

    raw = [
        {
            "issuer_code": entity_id,
            "sales": Decimal("2000000"),
            "fiscal_start": "2025-01-01",
            "fiscal_end": "2025-03-31",
            "currency": "USD",
            "provenance_id": source_id,
        }
    ]
    connector = MockProviderBConnector(raw_records=raw)
    canonical = connector.normalize(connector.fetch())

    assert len(canonical) == 1
    fact = canonical[0]
    assert fact.entity_id == entity_id
    assert fact.fact_type == "revenue"
    assert fact.value_numeric == Decimal("2000000")
    assert fact.currency == "USD"
    assert fact.source_id == source_id


def test_both_providers_produce_same_canonical_shape(client):
    entity_id = create_entity(client).json()["id"]
    source_id = create_source(client).json()["id"]

    raw_a = [{
        "company_id": entity_id,
        "revenue": Decimal("500"),
        "period_start": "2025-01-01",
        "period_end": "2025-03-31",
        "currency_code": "USD",
        "source_ref": source_id,
    }]
    raw_b = [{
        "issuer_code": entity_id,
        "sales": Decimal("500"),
        "fiscal_start": "2025-01-01",
        "fiscal_end": "2025-03-31",
        "currency": "USD",
        "provenance_id": source_id,
    }]

    canonical_a = MockProviderAConnector(raw_records=raw_a).normalize(raw_a)
    canonical_b = MockProviderBConnector(raw_records=raw_b).normalize(raw_b)

    assert canonical_a[0].entity_id == canonical_b[0].entity_id
    assert canonical_a[0].fact_type == canonical_b[0].fact_type
    assert canonical_a[0].value_numeric == canonical_b[0].value_numeric
    assert canonical_a[0].period_start == canonical_b[0].period_start
    assert canonical_a[0].period_end == canonical_b[0].period_end
    assert canonical_a[0].currency == canonical_b[0].currency
    assert canonical_a[0].source_id == canonical_b[0].source_id


def test_provider_specific_fields_do_not_leak_into_canonical(client):
    entity_id = create_entity(client).json()["id"]
    raw = [{
        "company_id": entity_id,
        "revenue": Decimal("100"),
        "period_start": "2025-01-01",
        "period_end": "2025-03-31",
    }]
    canonical = MockProviderAConnector(raw_records=raw).normalize(raw)

    fact_fields = vars(canonical[0]).keys()
    assert "company_id" not in fact_fields
    assert "revenue" not in fact_fields
    assert "issuer_code" not in fact_fields


def test_provider_a_rejects_incomplete_record():
    raw = [{"company_id": 1, "revenue": Decimal("100")}]
    connector = MockProviderAConnector(raw_records=raw)
    try:
        connector.normalize(raw)
        assert False, "Expected ValueError for missing required fields"
    except ValueError:
        pass


def test_ingestion_persists_canonical_facts(db_session, client):
    entity_id = create_entity(client).json()["id"]
    raw = [{
        "company_id": entity_id,
        "revenue": Decimal("42"),
        "period_start": "2025-01-01",
        "period_end": "2025-03-31",
    }]
    canonical = MockProviderAConnector(raw_records=raw).normalize(raw)

    created = ingest_canonical_facts(db_session, canonical)
    assert len(created) == 1
    assert created[0].entity_id == entity_id
    assert created[0].fact_type == "revenue"


def test_ingestion_rejects_nonexistent_entity(db_session):
    from app.data.contracts.financial_fact import CanonicalFinancialFact
    from decimal import Decimal as D

    bad_fact = CanonicalFinancialFact(
        entity_id=999999, fact_type="revenue", value_numeric=D("100")
    )
    try:
        ingest_canonical_facts(db_session, [bad_fact])
        assert False, "Expected IngestionValidationError"
    except IngestionValidationError:
        pass


def test_ingestion_rejects_nonexistent_source(db_session, client):
    from app.data.contracts.financial_fact import CanonicalFinancialFact
    from decimal import Decimal as D

    entity_id = create_entity(client).json()["id"]
    bad_fact = CanonicalFinancialFact(
        entity_id=entity_id,
        fact_type="revenue",
        value_numeric=D("100"),
        source_id=999999,
    )
    try:
        ingest_canonical_facts(db_session, [bad_fact])
        assert False, "Expected IngestionValidationError"
    except IngestionValidationError:
        pass


def test_temporal_fields_preserved_through_ingestion(db_session, client):
    entity_id = create_entity(client).json()["id"]
    raw = [{
        "company_id": entity_id,
        "revenue": Decimal("99"),
        "period_start": "2025-04-01",
        "period_end": "2025-06-30",
    }]
    canonical = MockProviderAConnector(raw_records=raw).normalize(raw)
    created = ingest_canonical_facts(db_session, canonical)

    from datetime import date
    assert created[0].period_start == date(2025, 4, 1)
    assert created[0].period_end == date(2025, 6, 30)


def test_existing_source_behavior_unaffected(client):
    response = create_source(client)
    assert response.status_code == 201