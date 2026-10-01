import pytest
from sqlalchemy.exc import IntegrityError

from app.models.event import Event
from app.models.financial_fact import FinancialFact


def make_entity(client, name="Obs Co"):
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


def test_financial_fact_defaults_to_observed(client):
    entity_id = make_entity(client)
    response = client.post(
        "/financial-facts",
        json={"entity_id": entity_id, "fact_type": "revenue", "value_numeric": "100"},
    )
    assert response.json()["observation_kind"] == "observed"


def test_financial_fact_accepts_derived(client):
    entity_id = make_entity(client)
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "gross_margin",
            "value_numeric": "0.42",
            "observation_kind": "derived",
        },
    )
    assert response.status_code == 201
    assert response.json()["observation_kind"] == "derived"


def test_financial_fact_accepts_inferred(client):
    entity_id = make_entity(client)
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "estimated_revenue",
            "value_numeric": "100",
            "observation_kind": "inferred",
        },
    )
    assert response.status_code == 201
    assert response.json()["observation_kind"] == "inferred"


def test_financial_fact_rejects_invalid_observation_kind(client):
    entity_id = make_entity(client)
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "revenue",
            "value_numeric": "100",
            "observation_kind": "guessed",
        },
    )
    assert response.status_code == 422


def test_event_defaults_to_observed(client):
    entity_id = make_entity(client)
    response = client.post(
        "/events",
        json={"entity_id": entity_id, "event_type": "leadership_change", "description": "x"},
    )
    assert response.json()["observation_kind"] == "observed"


def test_event_accepts_derived_and_inferred(client):
    entity_id = make_entity(client)
    derived = client.post(
        "/events",
        json={
            "entity_id": entity_id,
            "event_type": "pattern_detected",
            "description": "x",
            "observation_kind": "derived",
        },
    )
    inferred = client.post(
        "/events",
        json={
            "entity_id": entity_id,
            "event_type": "suspected_change",
            "description": "x",
            "observation_kind": "inferred",
        },
    )
    assert derived.json()["observation_kind"] == "derived"
    assert inferred.json()["observation_kind"] == "inferred"


def test_database_rejects_invalid_observation_kind_on_financial_fact(client, db_session):
    entity_id = make_entity(client)
    fact = FinancialFact(
        entity_id=entity_id, fact_type="x", value_numeric=1, observation_kind="guessed"
    )
    db_session.add(fact)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_rejects_invalid_observation_kind_on_event(client, db_session):
    entity_id = make_entity(client)
    event = Event(
        entity_id=entity_id, event_type="x", description="x", observation_kind="guessed"
    )
    db_session.add(event)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()