def create_research_case(client, **overrides):
    payload = {
        "entity_id": None,
        "title": "Source test case",
        "description": "Test case",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/research-cases", json=payload)


def create_claim(client, case_id, **overrides):
    payload = {
        "entity_id": None,
        "statement": "Test claim needing evidence",
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


def create_source(client, **overrides):
    payload = {
        "title": "Test Source",
        "url": "https://example.com/article",
        "publisher": "Example Publisher",
        "source_type": "news",
    }
    payload.update(overrides)
    return client.post("/research-sources", json=payload)


def test_create_source(client):
    response = create_source(client)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Source"
    assert data["source_type"] == "news"


def test_list_sources(client):
    create_source(client, title="Source A")
    create_source(client, title="Source B")
    response = client.get("/research-sources")
    assert response.status_code == 200
    titles = [s["title"] for s in response.json()]
    assert "Source A" in titles
    assert "Source B" in titles


def test_get_source_by_id(client):
    created = create_source(client).json()
    response = client.get(f"/research-sources/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_nonexistent_source_returns_404(client):
    response = client.get("/research-sources/999999")
    assert response.status_code == 404


def test_create_source_rejects_invalid_source_type(client):
    response = create_source(client, source_type="not_a_real_type")
    assert response.status_code == 422


def test_attach_source_to_claim(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    source_id = create_source(client).json()["id"]

    response = client.post(
        f"/claims/{claim_id}/sources",
        json={
            "source_id": source_id,
            "relationship_type": "supports",
            "excerpt": "some text",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["claim_id"] == claim_id
    assert data["source_id"] == source_id
    assert data["relationship_type"] == "supports"
    assert data["source"]["title"] == "Test Source"


def test_attach_source_rejects_invalid_relationship_type(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    source_id = create_source(client).json()["id"]

    response = client.post(
        f"/claims/{claim_id}/sources",
        json={"source_id": source_id, "relationship_type": "not_real"},
    )
    assert response.status_code == 422


def test_attach_source_to_nonexistent_claim_returns_404(client):
    source_id = create_source(client).json()["id"]
    response = client.post(
        "/claims/999999/sources",
        json={"source_id": source_id, "relationship_type": "supports"},
    )
    assert response.status_code == 404


def test_attach_nonexistent_source_returns_404(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    response = client.post(
        f"/claims/{claim_id}/sources",
        json={"source_id": 999999, "relationship_type": "supports"},
    )
    assert response.status_code == 404


def test_duplicate_claim_source_attachment_rejected(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    source_id = create_source(client).json()["id"]

    client.post(
        f"/claims/{claim_id}/sources",
        json={"source_id": source_id, "relationship_type": "supports"},
    )
    response = client.post(
        f"/claims/{claim_id}/sources",
        json={"source_id": source_id, "relationship_type": "context"},
    )
    assert response.status_code == 409


def test_list_sources_for_claim(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    source_id = create_source(client).json()["id"]

    client.post(
        f"/claims/{claim_id}/sources",
        json={"source_id": source_id, "relationship_type": "context"},
    )
    response = client.get(f"/claims/{claim_id}/sources")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source"]["id"] == source_id


def test_list_claims_for_source(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    source_id = create_source(client).json()["id"]

    client.post(
        f"/claims/{claim_id}/sources",
        json={"source_id": source_id, "relationship_type": "supports"},
    )
    response = client.get(f"/research-sources/{source_id}/claims")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["claim_id"] == claim_id


def test_detach_source_from_claim(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    source_id = create_source(client).json()["id"]

    client.post(
        f"/claims/{claim_id}/sources",
        json={"source_id": source_id, "relationship_type": "supports"},
    )
    response = client.delete(f"/claims/{claim_id}/sources/{source_id}")
    assert response.status_code == 204

    verify = client.get(f"/claims/{claim_id}/sources")
    assert verify.json() == []


def test_detach_nonexistent_claim_source_returns_404(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    source_id = create_source(client).json()["id"]

    response = client.delete(f"/claims/{claim_id}/sources/{source_id}")
    assert response.status_code == 404


def test_existing_claim_behavior_unaffected(client):
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    response = client.get(f"/claims/{claim_id}")
    assert response.status_code == 200
    assert response.json()["id"] == claim_id