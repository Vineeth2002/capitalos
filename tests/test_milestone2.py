def create_research_case(client, **overrides):
    payload = {
        "entity_id": None,
        "title": "Relationship test case",
        "description": "Test case",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/research-cases", json=payload)


def create_claim(client, case_id, **overrides):
    payload = {
        "entity_id": None,
        "statement": "Test claim statement",
        "temporal_orientation": "current",
        "epistemic_role": "evidence",
        "shape": "qualitative",
        "confidence_band": None,
        "lifecycle_status": "active",
        "lens": None,
        "origin": "user",
    }
    payload.update(overrides)
    return client.post(f"/research-cases/{case_id}/claims", json=payload)


def setup_two_claims(client):
    case_id = create_research_case(client).json()["id"]
    claim_a = create_claim(client, case_id, statement="Claim A").json()
    claim_b = create_claim(client, case_id, statement="Claim B").json()
    return claim_a["id"], claim_b["id"]


def test_create_relationship(client):
    claim_a_id, claim_b_id = setup_two_claims(client)
    response = client.post(
        f"/claims/{claim_a_id}/relationships",
        json={"to_claim_id": claim_b_id, "relationship_type": "contradicts"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["from_claim_id"] == claim_a_id
    assert data["to_claim_id"] == claim_b_id
    assert data["relationship_type"] == "contradicts"


def test_relationship_rejects_self_reference(client):
    claim_a_id, _ = setup_two_claims(client)
    response = client.post(
        f"/claims/{claim_a_id}/relationships",
        json={"to_claim_id": claim_a_id, "relationship_type": "supports"},
    )
    assert response.status_code == 422


def test_relationship_rejects_nonexistent_target(client):
    claim_a_id, _ = setup_two_claims(client)
    response = client.post(
        f"/claims/{claim_a_id}/relationships",
        json={"to_claim_id": 999999, "relationship_type": "supports"},
    )
    assert response.status_code == 404


def test_relationship_rejects_nonexistent_source_claim(client):
    response = client.post(
        "/claims/999999/relationships",
        json={"to_claim_id": 1, "relationship_type": "supports"},
    )
    assert response.status_code == 404


def test_list_relationships_for_claim(client):
    claim_a_id, claim_b_id = setup_two_claims(client)
    client.post(
        f"/claims/{claim_a_id}/relationships",
        json={"to_claim_id": claim_b_id, "relationship_type": "supports"},
    )
    response = client.get(f"/claims/{claim_a_id}/relationships")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["to_claim_id"] == claim_b_id