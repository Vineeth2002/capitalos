def test_create_classification(client):
    response = client.post(
        "/fact-classifications",
        json={
            "applies_to": "financial_fact",
            "type_name": "revenue",
            "category": "income_statement",
            "description": "Total revenue for the period",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["applies_to"] == "financial_fact"
    assert data["type_name"] == "revenue"


def test_duplicate_classification_rejected(client):
    payload = {"applies_to": "financial_fact", "type_name": "revenue"}
    assert client.post("/fact-classifications", json=payload).status_code == 201
    assert client.post("/fact-classifications", json=payload).status_code == 409


def test_same_type_name_different_applies_to_allowed(client):
    assert client.post(
        "/fact-classifications",
        json={"applies_to": "financial_fact", "type_name": "dividend"},
    ).status_code == 201
    assert client.post(
        "/fact-classifications",
        json={"applies_to": "event", "type_name": "dividend"},
    ).status_code == 201


def test_invalid_applies_to_rejected(client):
    response = client.post(
        "/fact-classifications",
        json={"applies_to": "not_real", "type_name": "revenue"},
    )
    assert response.status_code == 422


def test_list_classifications_filtered_by_applies_to(client):
    client.post("/fact-classifications", json={"applies_to": "financial_fact", "type_name": "a"})
    client.post("/fact-classifications", json={"applies_to": "event", "type_name": "b"})

    only_facts = client.get("/fact-classifications", params={"applies_to": "financial_fact"}).json()
    assert len(only_facts) == 1
    assert only_facts[0]["type_name"] == "a"


def test_unregistered_fact_type_still_works(client):
    entity = client.post(
        "/entities",
        json={
            "entity_type": "company",
            "canonical_name": "Unclassified Co",
            "ticker": None,
            "exchange": None,
            "status": "active",
        },
    ).json()
    response = client.post(
        "/financial-facts",
        json={
            "entity_id": entity["id"],
            "fact_type": "totally_unregistered_type_xyz",
            "value_numeric": "1",
        },
    )
    assert response.status_code == 201