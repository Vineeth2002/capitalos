from app.services import reasoning_intake_service
from app.services.reasoning_intake_service import IntakeUnavailableError


def fake_call_llm(text):
    return {
        "objective_context": "Wants a stable, respected long-term career.",
        "draft_claims": [
            {
                "statement": "RBI Grade B offers more prestige than SSC CGL",
                "temporal_orientation": "current",
                "epistemic_role": "assumption",
                "shape": "qualitative",
            }
        ],
        "inferred_candidates": [
            {
                "statement": "May be spreading preparation across too many exams at once",
                "reason": "Multiple exam paths were mentioned without a clear single priority",
            }
        ],
    }


def fake_call_llm_with_invalid_entries(text):
    return {
        "objective_context": "Some objective",
        "draft_claims": [
            {
                "statement": "Valid claim",
                "temporal_orientation": "current",
                "epistemic_role": "assumption",
                "shape": "qualitative",
            },
            {
                "statement": "Invalid claim - bad enum",
                "temporal_orientation": "someday",
                "epistemic_role": "assumption",
                "shape": "qualitative",
            },
        ],
        "inferred_candidates": [],
    }


def failing_call_llm(text):
    raise IntakeUnavailableError("Simulated exhausted-retry failure")


def test_reasoning_intake_returns_structured_draft(client, monkeypatch):
    monkeypatch.setattr(reasoning_intake_service, "_call_llm", fake_call_llm)

    response = client.post(
        "/reasoning-intake",
        json={"text": "I'm torn between RBI Grade B and SSC CGL right now."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["objective_context"] == "Wants a stable, respected long-term career."
    assert len(data["draft_claims"]) == 1
    assert data["draft_claims"][0]["epistemic_role"] == "assumption"
    assert len(data["inferred_candidates"]) == 1
    assert "reason" in data["inferred_candidates"][0]


def test_reasoning_intake_drops_invalid_enum_values(client, monkeypatch):
    monkeypatch.setattr(
        reasoning_intake_service, "_call_llm", fake_call_llm_with_invalid_entries
    )

    response = client.post("/reasoning-intake", json={"text": "Some reasoning"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["draft_claims"]) == 1
    assert data["draft_claims"][0]["statement"] == "Valid claim"


def test_reasoning_intake_rejects_empty_text(client):
    response = client.post("/reasoning-intake", json={"text": "   "})
    assert response.status_code == 422


def test_reasoning_intake_returns_503_when_provider_unavailable(client, monkeypatch):
    monkeypatch.setattr(reasoning_intake_service, "_call_llm", failing_call_llm)

    response = client.post("/reasoning-intake", json={"text": "Some reasoning"})
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"].lower()