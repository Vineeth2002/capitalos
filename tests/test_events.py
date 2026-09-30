from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.event import Event


def make_entity(client, name="Event Co"):
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


def make_security(client, issuer_id, identifier="INE222A01012"):
    return client.post(
        "/securities",
        json={"issuer_entity_id": issuer_id, "identifier_type": "ISIN", "identifier": identifier},
    ).json()["id"]


def make_listing(client, security_id, exchange="NSE", symbol="EVT"):
    return client.post(
        "/listings",
        json={"security_id": security_id, "exchange": exchange, "symbol": symbol},
    ).json()["id"]


def post_event(client, **overrides):
    payload = {"event_type": "leadership_change", "description": "CEO resigned"}
    payload.update(overrides)
    return client.post("/events", json=payload)


# ---- subject integrity ----

def test_entity_only_subject_valid(client):
    entity_id = make_entity(client)
    response = post_event(client, entity_id=entity_id)
    assert response.status_code == 201
    assert response.json()["entity_id"] == entity_id


def test_security_only_subject_valid(client):
    security_id = make_security(client, make_entity(client))
    response = post_event(
        client, security_id=security_id, event_type="dividend_declared",
        description="Dividend of 5 per share declared"
    )
    assert response.status_code == 201
    assert response.json()["security_id"] == security_id


def test_listing_only_subject_valid(client):
    listing_id = make_listing(client, make_security(client, make_entity(client)))
    response = post_event(
        client, listing_id=listing_id, event_type="trading_halt",
        description="Trading halted for volatility"
    )
    assert response.status_code == 201
    assert response.json()["listing_id"] == listing_id


def test_zero_subjects_rejected(client):
    assert post_event(client).status_code == 422


def test_two_subjects_rejected(client):
    entity_id = make_entity(client)
    security_id = make_security(client, entity_id)
    response = post_event(client, entity_id=entity_id, security_id=security_id)
    assert response.status_code == 422


def test_three_subjects_rejected(client):
    entity_id = make_entity(client)
    security_id = make_security(client, entity_id)
    listing_id = make_listing(client, security_id)
    response = post_event(
        client, entity_id=entity_id, security_id=security_id, listing_id=listing_id
    )
    assert response.status_code == 422


def test_nonexistent_security_and_listing_rejected(client):
    assert post_event(client, security_id=999999).status_code == 404
    assert post_event(client, listing_id=999999).status_code == 404


def test_database_check_rejects_zero_two_and_three_subjects(client, db_session):
    entity_id = make_entity(client)
    security_id = make_security(client, entity_id)
    listing_id = make_listing(client, security_id)

    bad_rows = [
        Event(event_type="x", description="x"),
        Event(event_type="x", description="x", entity_id=entity_id, security_id=security_id),
        Event(
            event_type="x", description="x",
            entity_id=entity_id, security_id=security_id, listing_id=listing_id,
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
    post_event(client, security_id=security_id, event_type="dividend_declared", description="d")
    post_event(client, listing_id=listing_id, event_type="trading_halt", description="h")

    by_security = client.get("/events", params={"security_id": security_id}).json()
    by_listing = client.get("/events", params={"listing_id": listing_id}).json()
    assert len(by_security) == 1
    assert len(by_listing) == 1


def test_filters_by_event_type(client):
    entity_id = make_entity(client)
    post_event(client, entity_id=entity_id, event_type="leadership_change", description="a")
    post_event(client, entity_id=entity_id, event_type="merger_announced", description="b")

    filtered = client.get("/events", params={"event_type": "merger_announced"}).json()
    assert len(filtered) == 1
    assert filtered[0]["event_type"] == "merger_announced"


# ---- time ----

def test_event_date_persists(client):
    entity_id = make_entity(client)
    data = post_event(client, entity_id=entity_id, event_date="2025-06-15").json()
    assert data["event_date"] == "2025-06-15"


def test_event_date_is_optional(client):
    entity_id = make_entity(client)
    data = post_event(client, entity_id=entity_id).json()
    assert data["event_date"] is None


def test_published_at_and_recorded_at_persist(client):
    entity_id = make_entity(client)
    data = post_event(client, entity_id=entity_id, published_at="2025-05-01T09:30:00").json()
    assert data["published_at"] == "2025-05-01T09:30:00"
    assert data["recorded_at"] is not None


def test_aware_published_at_is_stored_as_naive_utc(client):
    entity_id = make_entity(client)
    data = post_event(
        client, entity_id=entity_id, published_at="2025-01-01T10:00:00+05:30"
    ).json()
    assert data["published_at"] == "2025-01-01T04:30:00"


# ---- supersession ----

def test_valid_correction_leaves_old_row_unchanged(client):
    entity_id = make_entity(client)
    original = post_event(
        client, entity_id=entity_id, event_type="leadership_change",
        description="CFO resigned (unconfirmed)"
    ).json()
    before = client.get(f"/events/{original['id']}").json()

    correction = post_event(
        client,
        entity_id=entity_id,
        event_type="leadership_change",
        description="CFO resignation confirmed, effective next quarter",
        supersedes_id=original["id"],
        supersession_reason="Initial report was unconfirmed rumor",
    )
    assert correction.status_code == 201
    assert correction.json()["supersedes_id"] == original["id"]

    after = client.get(f"/events/{original['id']}").json()
    assert after == before
    assert after["supersedes_id"] is None


def test_supersede_nonexistent_target_rejected(client):
    entity_id = make_entity(client)
    assert post_event(client, entity_id=entity_id, supersedes_id=999999).status_code == 404


def test_supersede_subject_mismatch_rejected(client):
    entity_a = make_entity(client, "A Co")
    entity_b = make_entity(client, "B Co")
    original = post_event(client, entity_id=entity_a).json()
    response = post_event(client, entity_id=entity_b, supersedes_id=original["id"])
    assert response.status_code == 422


def test_supersede_event_type_mismatch_rejected(client):
    entity_id = make_entity(client)
    original = post_event(client, entity_id=entity_id, event_type="leadership_change").json()
    response = post_event(
        client, entity_id=entity_id, event_type="merger_announced",
        supersedes_id=original["id"]
    )
    assert response.status_code == 422


def test_already_superseded_target_rejected(client):
    entity_id = make_entity(client)
    original = post_event(client, entity_id=entity_id).json()
    assert post_event(client, entity_id=entity_id, supersedes_id=original["id"]).status_code == 201
    assert post_event(client, entity_id=entity_id, supersedes_id=original["id"]).status_code == 409


def test_database_rejects_self_supersession(client, db_session):
    entity_id = make_entity(client)
    event = Event(event_type="x", description="x", entity_id=entity_id)
    db_session.add(event)
    db_session.commit()
    event.supersedes_id = event.id
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_enforces_unique_supersedes_id(client, db_session):
    entity_id = make_entity(client)
    original = Event(event_type="x", description="x", entity_id=entity_id)
    db_session.add(original)
    db_session.commit()
    db_session.add(
        Event(event_type="x", description="y", entity_id=entity_id, supersedes_id=original.id)
    )
    db_session.commit()
    db_session.add(
        Event(event_type="x", description="z", entity_id=entity_id, supersedes_id=original.id)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---- provenance ----

def test_source_id_and_source_record_id_validated(client):
    entity_id = make_entity(client)
    assert post_event(client, entity_id=entity_id, source_id=999999).status_code == 404
    assert post_event(client, entity_id=entity_id, source_record_id=999999).status_code == 404


def test_get_and_list_events(client):
    entity_id = make_entity(client)
    created = post_event(client, entity_id=entity_id).json()

    assert client.get(f"/events/{created['id']}").status_code == 200
    assert len(client.get("/events", params={"entity_id": entity_id}).json()) == 1
    assert client.get("/events/999999").status_code == 404