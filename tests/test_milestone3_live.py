import os

import pytest


LIVE = os.environ.get("RUN_LIVE_LLM_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE,
    reason=(
        "Live LLM tests are skipped by default to avoid burning Gemini "
        "free-tier quota (5 requests/minute). Set RUN_LIVE_LLM_TESTS=1 "
        "to run this against the real model."
    ),
)


def create_research_case(client, **overrides):
    payload = {
        "entity_id": None,
        "title": "Live challenger test case",
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


FORBIDDEN_PHRASES = [
    "you should buy",
    "you should sell",
    "recommend buying",
    "recommend selling",
    "best decision is",
    "avoid this investment",
]


def test_live_generate_challenges_avoids_forbidden_language(client):
    case_id = create_research_case(client).json()["id"]
    create_claim(client, case_id)

    response = client.post(f"/research-cases/{case_id}/challenge")
    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 1
    for challenge in data:
        lowered = challenge["text"].lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in lowered