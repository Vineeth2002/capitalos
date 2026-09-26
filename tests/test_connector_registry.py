from decimal import Decimal
from datetime import date

import pytest

from app.data.connectors.base import FinancialDataConnector
from app.data.connectors.registry import (
    register_connector,
    get_connector_class,
    list_registered_providers,
    clear_registry,
)
import app.data.connectors  # noqa: F401 - runs registration side effects for A and B
from app.data.contracts.financial_fact import CanonicalFinancialFact
from app.data.ingestion.service import ingest_from_provider


def create_entity(client, **overrides):
    payload = {
        "entity_type": "company",
        "canonical_name": "Registry Test Corp",
        "ticker": "RTC",
        "exchange": "NASDAQ",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/entities", json=payload)


def test_mock_provider_a_and_b_are_registered():
    providers = list_registered_providers()
    assert "mock_provider_a" in providers
    assert "mock_provider_b" in providers


def test_get_connector_class_by_name():
    connector_class = get_connector_class("mock_provider_a")
    assert connector_class.provider_name == "mock_provider_a"


def test_unknown_provider_raises_key_error():
    with pytest.raises(KeyError):
        get_connector_class("does_not_exist_provider")


class MockProviderCConnector(FinancialDataConnector):
    """
    A third, throwaway mock provider defined ONLY in this test file, using
    yet another set of field names, to prove a brand-new provider can be
    registered and ingested without touching FinancialFact, the ingestion
    service, or the canonical fact contract.
    """

    provider_name = "mock_provider_c"

    def __init__(self, raw_records=None):
        self._raw_records = raw_records if raw_records is not None else []

    def fetch(self):
        return self._raw_records

    def normalize(self, raw_records):
        canonical = []
        for record in raw_records:
            canonical.append(
                CanonicalFinancialFact(
                    entity_id=record["entity_ref"],
                    fact_type="revenue",
                    value_numeric=record["total_income"],
                    period_start=record["from_date"],
                    period_end=record["to_date"],
                )
            )
        return canonical


def test_third_provider_can_be_registered_and_used(client, db_session):
    register_connector(MockProviderCConnector.provider_name, MockProviderCConnector)

    entity_id = create_entity(client).json()["id"]
    raw = [
        {
            "entity_ref": entity_id,
            "total_income": Decimal("777"),
            "from_date": date(2025, 7, 1),
            "to_date": date(2025, 9, 30),
        }
    ]

    created = ingest_from_provider(db_session, "mock_provider_c", raw)

    assert len(created) == 1
    assert created[0].entity_id == entity_id
    assert created[0].fact_type == "revenue"
    assert created[0].value_numeric == Decimal("777")

    clear_registry()
    import app.data.connectors  # noqa: F401 - re-registers A and B for other tests