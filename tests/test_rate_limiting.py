from app.services import challenger_service


def create_research_case(client, **overrides):
    payload = {
        "entity_id": None,
        "title": "Rate limit test case",
        "description": "Test case",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/research-cases", json=payload)


def create_claim(client, case_id, **overrides):
    payload = {
        "entity_id": None,
        "statement": "Test claim for rate limiting",
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


def fake_call_llm(claims, relationships):
    return [
        {
            "category": "missing_evidence",
            "text": "Mocked challenge for rate limit testing.",
            "claim_ids": [claims[0].id],
        }
    ]


def test_challenge_allows_up_to_limit_then_blocks(client, monkeypatch):
    monkeypatch.setattr(challenger_service, "_call_llm", fake_call_llm)

    case_id = create_research_case(client).json()["id"]
    create_claim(client, case_id)

    for i in range(5):
        response = client.post(f"/research-cases/{case_id}/challenge")
        assert response.status_code == 200

    sixth = client.post(f"/research-cases/{case_id}/challenge")
    assert sixth.status_code == 429
    assert "rate limit" in sixth.json()["detail"].lower()


def test_rate_limit_does_not_block_other_endpoints(client, monkeypatch):
    monkeypatch.setattr(challenger_service, "_call_llm", fake_call_llm)

    case_id = create_research_case(client).json()["id"]
    create_claim(client, case_id)

    for _ in range(5):
        client.post(f"/research-cases/{case_id}/challenge")

    blocked = client.post(f"/research-cases/{case_id}/challenge")
    assert blocked.status_code == 429

    still_works = client.get(f"/research-cases/{case_id}/claims")
    assert still_works.status_code == 200