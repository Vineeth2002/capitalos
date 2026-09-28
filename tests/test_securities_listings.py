import pytest
from sqlalchemy.exc import IntegrityError

from app.models.listing import Listing
from app.models.security import Security


def create_entity(client, entity_type="company", name="Issuer Co"):
    return client.post(
        "/entities",
        json={
            "entity_type": entity_type,
            "canonical_name": name,
            "ticker": None,
            "exchange": None,
            "status": "active",
        },
    )


def create_security(client, issuer_id, **overrides):
    payload = {
        "issuer_entity_id": issuer_id,
        "identifier_type": "ISIN",
        "identifier": "INE000A01010",
    }
    payload.update(overrides)
    return client.post("/securities", json=payload)


def test_create_security_with_company_issuer(client):
    issuer_id = create_entity(client).json()["id"]
    response = create_security(client, issuer_id)
    assert response.status_code == 201
    data = response.json()
    assert data["issuer_entity_id"] == issuer_id
    assert data["identifier_type"] == "ISIN"


def test_security_rejects_non_company_issuer(client):
    person_id = create_entity(client, entity_type="person", name="A Person").json()["id"]
    response = create_security(client, person_id)
    assert response.status_code == 422


def test_security_rejects_nonexistent_issuer(client):
    response = create_security(client, 999999)
    assert response.status_code == 404


def test_security_duplicate_identifier_rejected(client):
    issuer_id = create_entity(client).json()["id"]
    assert create_security(client, issuer_id).status_code == 201
    assert create_security(client, issuer_id).status_code == 409


def test_security_identifier_requires_type(client):
    issuer_id = create_entity(client).json()["id"]
    response = create_security(client, issuer_id, identifier_type=None)
    assert response.status_code == 422


def test_securities_without_identifier_are_allowed(client):
    issuer_id = create_entity(client).json()["id"]
    first = create_security(client, issuer_id, identifier_type=None, identifier=None)
    second = create_security(client, issuer_id, identifier_type=None, identifier=None)
    assert first.status_code == 201
    assert second.status_code == 201


def test_security_identifier_unique_at_database_level(client, db_session):
    issuer_id = create_entity(client).json()["id"]
    db_session.add(Security(issuer_entity_id=issuer_id, identifier_type="ISIN", identifier="X1"))
    db_session.commit()
    db_session.add(Security(issuer_entity_id=issuer_id, identifier_type="ISIN", identifier="X1"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_get_and_list_securities(client):
    issuer_id = create_entity(client).json()["id"]
    created = create_security(client, issuer_id).json()

    got = client.get(f"/securities/{created['id']}")
    assert got.status_code == 200
    assert got.json()["id"] == created["id"]

    listed = client.get("/securities")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    assert client.get("/securities/999999").status_code == 404


def test_create_listing_normalizes_exchange(client):
    issuer_id = create_entity(client).json()["id"]
    security_id = create_security(client, issuer_id).json()["id"]
    response = client.post(
        "/listings",
        json={"security_id": security_id, "exchange": " nse ", "symbol": "ABC"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["exchange"] == "NSE"
    assert data["symbol"] == "ABC"


def test_listing_missing_security_rejected(client):
    response = client.post(
        "/listings", json={"security_id": 999999, "exchange": "NSE", "symbol": "ABC"}
    )
    assert response.status_code == 404


def test_listing_duplicate_rejected(client):
    issuer_id = create_entity(client).json()["id"]
    security_id = create_security(client, issuer_id).json()["id"]
    payload = {"security_id": security_id, "exchange": "NSE", "symbol": "ABC"}
    assert client.post("/listings", json=payload).status_code == 201
    assert client.post("/listings", json={**payload, "exchange": "nse"}).status_code == 409


def test_same_security_can_list_on_multiple_exchanges(client):
    issuer_id = create_entity(client).json()["id"]
    security_id = create_security(client, issuer_id).json()["id"]
    nse = client.post(
        "/listings", json={"security_id": security_id, "exchange": "NSE", "symbol": "ABC"}
    )
    bse = client.post(
        "/listings", json={"security_id": security_id, "exchange": "BSE", "symbol": "500001"}
    )
    assert nse.status_code == 201
    assert bse.status_code == 201


def test_listing_unique_at_database_level(client, db_session):
    issuer_id = create_entity(client).json()["id"]
    security_id = create_security(client, issuer_id).json()["id"]
    db_session.add(Listing(security_id=security_id, exchange="NSE", symbol="ABC"))
    db_session.commit()
    db_session.add(Listing(security_id=security_id, exchange="NSE", symbol="ABC"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_get_and_list_listings(client):
    issuer_id = create_entity(client).json()["id"]
    security_id = create_security(client, issuer_id).json()["id"]
    created = client.post(
        "/listings", json={"security_id": security_id, "exchange": "NSE", "symbol": "ABC"}
    ).json()

    assert client.get(f"/listings/{created['id']}").status_code == 200
    assert len(client.get("/listings").json()) == 1
    assert client.get("/listings/999999").status_code == 404