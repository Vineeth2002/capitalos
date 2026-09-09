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


def create_research_case(client, entity_id=None, **overrides):
    payload = {
        "entity_id": entity_id,
        "title": "Initial thesis",
        "description": "Test case",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/research-cases", json=payload)


def valid_claim_payload(**overrides):
    payload = {
        "entity_id": None,
        "statement": "Margins may compress next year",
        "temporal_orientation": "forecast",
        "epistemic_role": "risk",
        "shape": "qualitative",
        "confidence_band": "medium",
        "lifecycle_status": "active",
        "lens": "fundamental",
        "origin": "user",
    }
    payload.update(overrides)
    return payload


def test_entity_creation(client):
    response = create_entity(client)
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_name"] == "Test Corp"
    assert data["entity_type"] == "company"
    assert "id" in data


def test_research_case_creation(client):
    entity_resp = create_entity(client)
    entity_id = entity_resp.json()["id"]

    response = create_research_case(client, entity_id=entity_id)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Initial thesis"
    assert data["entity_id"] == entity_id


def test_claim_creation(client):
    entity_resp = create_entity(client)
    entity_id = entity_resp.json()["id"]
    case_resp = create_research_case(client, entity_id=entity_id)
    case_id = case_resp.json()["id"]

    response = client.post(
        f"/research-cases/{case_id}/claims",
        json=valid_claim_payload(entity_id=entity_id),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["research_case_id"] == case_id
    assert data["temporal_orientation"] == "forecast"
    assert data["epistemic_role"] == "risk"
    assert data["shape"] == "qualitative"
    assert data["origin"] == "user"


def test_claim_enum_validation_rejects_invalid_value(client):
    case_resp = create_research_case(client)
    case_id = case_resp.json()["id"]

    bad_payload = valid_claim_payload(temporal_orientation="someday")
    response = client.post(f"/research-cases/{case_id}/claims", json=bad_payload)
    assert response.status_code == 422


def test_claim_belongs_to_research_case(client):
    case_a = create_research_case(client, title="Case A").json()
    case_b = create_research_case(client, title="Case B").json()

    client.post(f"/research-cases/{case_a['id']}/claims", json=valid_claim_payload())
    client.post(f"/research-cases/{case_b['id']}/claims", json=valid_claim_payload())

    response_a = client.get(f"/research-cases/{case_a['id']}/claims")
    claims_a = response_a.json()
    assert len(claims_a) == 1
    assert claims_a[0]["research_case_id"] == case_a["id"]

    response_b = client.get(f"/research-cases/{case_b['id']}/claims")
    claims_b = response_b.json()
    assert len(claims_b) == 1
    assert claims_b[0]["research_case_id"] == case_b["id"]

def test_delete_claim_succeeds_when_no_dependencies(client):
    case = create_research_case(client).json()
    claim_resp = client.post(
        f"/research-cases/{case['id']}/claims", json=valid_claim_payload()
    )
    claim_id = claim_resp.json()["id"]

    response = client.delete(f"/claims/{claim_id}")
    assert response.status_code == 204

    verify = client.get(f"/claims/{claim_id}")
    assert verify.status_code == 404


def test_delete_nonexistent_claim_returns_404(client):
    response = client.delete("/claims/999999")
    assert response.status_code == 404


def test_delete_claim_blocked_when_referenced_by_relationship(client):
    case = create_research_case(client).json()
    claim_a = client.post(
        f"/research-cases/{case['id']}/claims", json=valid_claim_payload()
    ).json()
    claim_b = client.post(
        f"/research-cases/{case['id']}/claims", json=valid_claim_payload()
    ).json()

    client.post(
        f"/claims/{claim_a['id']}/relationships",
        json={"to_claim_id": claim_b["id"], "relationship_type": "supports"},
    )

    response = client.delete(f"/claims/{claim_a['id']}")
    assert response.status_code == 409

    verify = client.get(f"/claims/{claim_a['id']}")
    assert verify.status_code == 200