def create_entity(client, **overrides):
    payload = {
        "entity_type": "company",
        "canonical_name": "Test Corp",
        "ticker": "TST",
        "exchange": "NASDAQ",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/entities", json=payload)


def create_source(client, **overrides):
    payload = {
        "title": "Test Filing",
        "url": "https://example.com/filing",
        "publisher": "SEC",
        "source_type": "filing",
    }
    payload.update(overrides)
    return client.post("/research-sources", json=payload)


def test_create_financial_fact(client):
    entity_id = create_entity(client).json()["id"]
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "revenue",
            "value_numeric": "1234567.891234",
            "unit": "USD",
            "currency": "USD",
            "period_start": "2025-01-01",
            "period_end": "2025-03-31",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["fact_type"] == "revenue"
    assert data["value_numeric"] == "1234567.891234"
    assert data["period_start"] == "2025-01-01"
    assert data["period_end"] == "2025-03-31"
    assert data["as_of_date"] is None


def test_retrieve_financial_fact(client):
    entity_id = create_entity(client).json()["id"]
    created = client.post(
        "/financial-facts",
        json={"entity_id": entity_id, "fact_type": "share_price", "value_numeric": "42.50"},
    ).json()

    response = client.get(f"/financial-facts/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_nonexistent_fact_returns_404(client):
    response = client.get("/financial-facts/999999")
    assert response.status_code == 404


def test_list_facts_filtered_by_entity(client):
    entity_a = create_entity(client, canonical_name="Company A").json()["id"]
    entity_b = create_entity(client, canonical_name="Company B").json()["id"]

    client.post(
        "/financial-facts",
        json={"entity_id": entity_a, "fact_type": "revenue", "value_numeric": "100"},
    )
    client.post(
        "/financial-facts",
        json={"entity_id": entity_b, "fact_type": "revenue", "value_numeric": "200"},
    )

    response = client.get("/financial-facts", params={"entity_id": entity_a})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["entity_id"] == entity_a


def test_list_facts_filtered_by_fact_type(client):
    entity_id = create_entity(client).json()["id"]

    client.post(
        "/financial-facts",
        json={"entity_id": entity_id, "fact_type": "revenue", "value_numeric": "100"},
    )
    client.post(
        "/financial-facts",
        json={"entity_id": entity_id, "fact_type": "share_price", "value_numeric": "50"},
    )

    response = client.get("/financial-facts", params={"fact_type": "share_price"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["fact_type"] == "share_price"


def test_create_fact_with_nonexistent_entity_returns_404(client):
    response = client.post(
        "/financial-facts",
        json={"entity_id": 999999, "fact_type": "revenue", "value_numeric": "100"},
    )
    assert response.status_code == 404


def test_create_fact_with_nonexistent_source_returns_404(client):
    entity_id = create_entity(client).json()["id"]
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "revenue",
            "value_numeric": "100",
            "source_id": 999999,
        },
    )
    assert response.status_code == 404


def test_create_fact_with_valid_nullable_source(client):
    entity_id = create_entity(client).json()["id"]
    source_id = create_source(client).json()["id"]

    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "revenue",
            "value_numeric": "500",
            "source_id": source_id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_id"] == source_id
    assert data["source"]["id"] == source_id


def test_fact_without_source_has_null_source(client):
    entity_id = create_entity(client).json()["id"]
    response = client.post(
        "/financial-facts",
        json={"entity_id": entity_id, "fact_type": "revenue", "value_numeric": "100"},
    )
    data = response.json()
    assert data["source_id"] is None
    assert data["source"] is None


def test_as_of_date_persists_for_point_in_time_fact(client):
    entity_id = create_entity(client).json()["id"]
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "share_price",
            "value_numeric": "99.99",
            "as_of_date": "2025-06-15",
        },
    )
    data = response.json()
    assert data["as_of_date"] == "2025-06-15"
    assert data["period_start"] is None
    assert data["period_end"] is None


def test_decimal_precision_is_preserved(client):
    entity_id = create_entity(client).json()["id"]
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "eps",
            "value_numeric": "3.141593",
        },
    )
    assert response.json()["value_numeric"] == "3.141593"


def test_invalid_numeric_value_rejected(client):
    entity_id = create_entity(client).json()["id"]
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity_id,
            "fact_type": "revenue",
            "value_numeric": "not_a_number",
        },
    )
    assert response.status_code == 422


def test_existing_source_behavior_unaffected(client):
    response = create_source(client)
    assert response.status_code == 201
    assert response.json()["title"] == "Test Filing"