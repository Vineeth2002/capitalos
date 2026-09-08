def test_confirm_creates_research_case_and_claims(client):
    payload = {
        "entity_id": None,
        "title": "Job offer vs skill-building decision",
        "description": "Objective: decide between accepting a stable job offer now vs spending months building AI/data science skills.",
        "claims": [
            {
                "statement": "The job offer is stable and provides immediate income",
                "temporal_orientation": "current",
                "epistemic_role": "evidence",
                "shape": "qualitative",
                "origin": "user",
            },
            {
                "statement": "Taking the job might reduce motivation to keep building AI/data science skills",
                "temporal_orientation": "forecast",
                "epistemic_role": "risk",
                "shape": "qualitative",
                "origin": "user",
            },
        ],
    }

    response = client.post("/reasoning-intake/confirm", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["research_case"]["title"] == "Job offer vs skill-building decision"
    assert len(data["claims"]) == 2
    assert data["claims"][0]["research_case_id"] == data["research_case"]["id"]
    assert data["claims"][1]["statement"].startswith("Taking the job")

    case_id = data["research_case"]["id"]
    verify = client.get(f"/research-cases/{case_id}/claims")
    assert verify.status_code == 200
    assert len(verify.json()) == 2


def test_confirm_rejects_empty_claims_list(client):
    payload = {
        "entity_id": None,
        "title": "Empty case",
        "description": None,
        "claims": [],
    }

    response = client.post("/reasoning-intake/confirm", json=payload)
    assert response.status_code == 422


def test_confirm_rolls_back_on_invalid_entity_reference(client):
    before = client.get("/research-cases").json()
    before_count = len(before)

    payload = {
        "entity_id": None,
        "title": "Should not be persisted",
        "description": "This entire request should fail atomically",
        "claims": [
            {
                "statement": "A valid claim that should NOT be saved",
                "temporal_orientation": "current",
                "epistemic_role": "evidence",
                "shape": "qualitative",
                "origin": "user",
            },
            {
                "entity_id": 999999,
                "statement": "A claim referencing a nonexistent entity",
                "temporal_orientation": "current",
                "epistemic_role": "evidence",
                "shape": "qualitative",
                "origin": "user",
            },
        ],
    }

    response = client.post("/reasoning-intake/confirm", json=payload)
    assert response.status_code == 404

    after = client.get("/research-cases").json()
    assert len(after) == before_count

    titles = [rc["title"] for rc in after]
    assert "Should not be persisted" not in titles
    