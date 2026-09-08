from app.services import challenger_service
from app.services import challenger_service


def create_research_case(client, **overrides):
    payload = {
        "entity_id": None,
        "title": "Challenger test case",
        "description": "Test case",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/research-cases", json=payload)


def create_claim(client, case_id, **overrides):
    payload = {
        "entity_id": None,
        "statement": "Margins are expected to expand next year",
        "temporal_orientation": "forecast",
        "epistemic_role": "hypothesis",
        "shape": "qualitative",
        "confidence_band": None,
        "lifecycle_status": "active",
        "lens": None,
        "origin": "user",
    }
    payload.update(overrides)
    return client.post(f"/research-cases/{case_id}/claims", json=payload)


VALID_CATEGORIES = {
    "missing_evidence",
    "unstated_assumption",
    "contradiction",
    "alternative_explanation",
    "invalidation_condition",
}


def fake_call_llm(claims, relationships):
    return [
        {
            "category": "missing_evidence",
            "text": "This claim lacks supporting evidence for the stated forecast.",
            "claim_ids": [claims[0].id],
        }
    ]


def fake_call_llm_multi(claims, relationships):
    claim_ids = [c.id for c in claims]
    return [
        {
            "category": "missing_evidence",
            "text": "First mocked challenge referencing the first claim.",
            "claim_ids": [claim_ids[0]],
        },
        {
            "category": "invalidation_condition",
            "text": "Second mocked challenge, a checkable question.",
            "claim_ids": claim_ids,
        },
    ]


def test_challenge_endpoint_requires_existing_case(client):
    response = client.post("/research-cases/999999/challenge")
    assert response.status_code == 404


def test_challenges_endpoint_requires_existing_case(client):
    response = client.get("/research-cases/999999/challenges")
    assert response.status_code == 404


def test_generate_challenges_with_no_claims_returns_empty(client):
    case_id = create_research_case(client).json()["id"]

    response = client.post(f"/research-cases/{case_id}/challenge")
    assert response.status_code == 200
    assert response.json() == []


def test_generate_challenges_returns_structured_output(client, monkeypatch):
    monkeypatch.setattr(challenger_service, "_call_llm", fake_call_llm)

    case_id = create_research_case(client).json()["id"]
    create_claim(client, case_id)

    response = client.post(f"/research-cases/{case_id}/challenge")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    challenge = data[0]
    assert challenge["category"] in VALID_CATEGORIES
    assert challenge["research_case_id"] == case_id
    assert isinstance(challenge["claim_ids"], list)
    assert len(challenge["claim_ids"]) >= 1
    assert isinstance(challenge["text"], str)
    assert len(challenge["text"]) > 0


def test_generate_challenges_links_multiple_claims(client, monkeypatch):
    monkeypatch.setattr(challenger_service, "_call_llm", fake_call_llm_multi)

    case_id = create_research_case(client).json()["id"]
    create_claim(client, case_id, statement="Claim A")
    create_claim(client, case_id, statement="Claim B")

    response = client.post(f"/research-cases/{case_id}/challenge")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert len(data[1]["claim_ids"]) == 2


def test_list_challenges_returns_previously_generated(client, monkeypatch):
    monkeypatch.setattr(challenger_service, "_call_llm", fake_call_llm)

    case_id = create_research_case(client).json()["id"]
    create_claim(client, case_id)

    client.post(f"/research-cases/{case_id}/challenge")
    response = client.get(f"/research-cases/{case_id}/challenges")

    assert response.status_code == 200
    assert len(response.json()) >= 1

from app.services.challenger_service import ChallengerUnavailableError

def failing_call_llm(claims, relationships):
    raise ChallengerUnavailableError("Simulated exhausted-retry failure")


def test_generate_challenges_returns_503_when_provider_unavailable(client, monkeypatch):
    monkeypatch.setattr(challenger_service, "_call_llm", failing_call_llm)

    case_id = create_research_case(client).json()["id"]
    create_claim(client, case_id)

    response = client.post(f"/research-cases/{case_id}/challenge")
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"].lower()