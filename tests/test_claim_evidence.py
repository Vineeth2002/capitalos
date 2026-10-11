def create_research_case(client, **overrides):
    payload = {
        "entity_id": None,
        "title": "Evidence test case",
        "description": "Test case",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/research-cases", json=payload)


def create_claim(client, case_id, **overrides):
    payload = {
        "entity_id": None,
        "statement": "Revenue grew significantly",
        "temporal_orientation": "current",
        "epistemic_role": "interpretation",
        "shape": "qualitative",
        "confidence_band": None,
        "lifecycle_status": "active",
        "lens": None,
        "origin": "user",
    }
    payload.update(overrides)
    return client.post(f"/research-cases/{case_id}/claims", json=payload)


def create_entity(client, **overrides):
    payload = {
        "entity_type": "company",
        "canonical_name": "Evidence Test Corp",
        "ticker": None,
        "exchange": None,
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/entities", json=payload)


def create_financial_fact(client, entity_id, **overrides):
    payload = {
        "entity_id": entity_id,
        "fact_type": "revenue",
        "value_numeric": "1000000",
    }
    payload.update(overrides)
    return client.post("/financial-facts", json=payload)


def create_event(client, entity_id, **overrides):
    payload = {
        "entity_id": entity_id,
        "event_type": "leadership_change",
        "description": "CEO resigned",
    }
    payload.update(overrides)
    return client.post("/events", json=payload)


def _setup_claim_and_entity(client):
    entity_id = create_entity(client).json()["id"]
    case_id = create_research_case(client).json()["id"]
    claim_id = create_claim(client, case_id).json()["id"]
    return entity_id, claim_id


def test_attach_financial_fact_as_evidence(client):
    entity_id, claim_id = _setup_claim_and_entity(client)
    fact_id = create_financial_fact(client, entity_id).json()["id"]

    response = client.post(
        f"/claims/{claim_id}/evidence",
        json={"financial_fact_id": fact_id, "relationship_type": "supports"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["claim_id"] == claim_id
    assert data["financial_fact_id"] == fact_id
    assert data["event_id"] is None
    assert data["financial_fact"]["id"] == fact_id
    assert data["event"] is None


def test_attach_event_as_evidence(client):
    entity_id, claim_id = _setup_claim_and_entity(client)
    event_id = create_event(client, entity_id).json()["id"]

    response = client.post(
        f"/claims/{claim_id}/evidence",
        json={"event_id": event_id, "relationship_type": "context"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == event_id
    assert data["financial_fact_id"] is None
    assert data["event"]["id"] == event_id


def test_zero_subjects_rejected(client):
    _, claim_id = _setup_claim_and_entity(client)
    response = client.post(
        f"/claims/{claim_id}/evidence", json={"relationship_type": "supports"}
    )
    assert response.status_code == 422


def test_two_subjects_rejected(client):
    entity_id, claim_id = _setup_claim_and_entity(client)
    fact_id = create_financial_fact(client, entity_id).json()["id"]
    event_id = create_event(client, entity_id).json()["id"]

    response = client.post(
        f"/claims/{claim_id}/evidence",
        json={
            "financial_fact_id": fact_id,
            "event_id": event_id,
            "relationship_type": "supports",
        },
    )
    assert response.status_code == 422


def test_nonexistent_claim_rejected(client):
    entity_id = create_entity(client).json()["id"]
    fact_id = create_financial_fact(client, entity_id).json()["id"]
    response = client.post(
        "/claims/999999/evidence",
        json={"financial_fact_id": fact_id, "relationship_type": "supports"},
    )
    assert response.status_code == 404


def test_nonexistent_financial_fact_rejected(client):
    _, claim_id = _setup_claim_and_entity(client)
    response = client.post(
        f"/claims/{claim_id}/evidence",
        json={"financial_fact_id": 999999, "relationship_type": "supports"},
    )
    assert response.status_code == 404


def test_nonexistent_event_rejected(client):
    _, claim_id = _setup_claim_and_entity(client)
    response = client.post(
        f"/claims/{claim_id}/evidence",
        json={"event_id": 999999, "relationship_type": "supports"},
    )
    assert response.status_code == 404


def test_duplicate_evidence_rejected(client):
    entity_id, claim_id = _setup_claim_and_entity(client)
    fact_id = create_financial_fact(client, entity_id).json()["id"]
    payload = {"financial_fact_id": fact_id, "relationship_type": "supports"}

    assert client.post(f"/claims/{claim_id}/evidence", json=payload).status_code == 201
    assert client.post(f"/claims/{claim_id}/evidence", json=payload).status_code == 409


def test_same_fact_can_be_evidence_for_different_claims(client):
    entity_id = create_entity(client).json()["id"]
    case_id = create_research_case(client).json()["id"]
    claim_a = create_claim(client, case_id, statement="Claim A").json()["id"]
    claim_b = create_claim(client, case_id, statement="Claim B").json()["id"]
    fact_id = create_financial_fact(client, entity_id).json()["id"]

    payload = {"financial_fact_id": fact_id, "relationship_type": "supports"}
    assert client.post(f"/claims/{claim_a}/evidence", json=payload).status_code == 201
    assert client.post(f"/claims/{claim_b}/evidence", json=payload).status_code == 201


def test_list_evidence_for_claim(client):
    entity_id, claim_id = _setup_claim_and_entity(client)
    fact_id = create_financial_fact(client, entity_id).json()["id"]
    event_id = create_event(client, entity_id).json()["id"]

    client.post(
        f"/claims/{claim_id}/evidence",
        json={"financial_fact_id": fact_id, "relationship_type": "supports"},
    )
    client.post(
        f"/claims/{claim_id}/evidence",
        json={"event_id": event_id, "relationship_type": "context"},
    )

    response = client.get(f"/claims/{claim_id}/evidence")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_evidence_for_nonexistent_claim_returns_404(client):
    response = client.get("/claims/999999/evidence")
    assert response.status_code == 404


def test_detach_evidence(client):
    entity_id, claim_id = _setup_claim_and_entity(client)
    fact_id = create_financial_fact(client, entity_id).json()["id"]
    created = client.post(
        f"/claims/{claim_id}/evidence",
        json={"financial_fact_id": fact_id, "relationship_type": "supports"},
    ).json()

    response = client.delete(f"/claims/{claim_id}/evidence/{created['id']}")
    assert response.status_code == 204

    verify = client.get(f"/claims/{claim_id}/evidence")
    assert verify.json() == []


def test_detach_nonexistent_evidence_returns_404(client):
    _, claim_id = _setup_claim_and_entity(client)
    response = client.delete(f"/claims/{claim_id}/evidence/999999")
    assert response.status_code == 404


def test_database_check_rejects_zero_and_two_subjects(client, db_session):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.models.claim_evidence import ClaimEvidence

    entity_id, claim_id = _setup_claim_and_entity(client)
    fact_id = create_financial_fact(client, entity_id).json()["id"]
    event_id = create_event(client, entity_id).json()["id"]

    bad_rows = [
        ClaimEvidence(claim_id=claim_id, relationship_type="supports"),
        ClaimEvidence(
            claim_id=claim_id,
            financial_fact_id=fact_id,
            event_id=event_id,
            relationship_type="supports",
        ),
    ]
    for row in bad_rows:
        db_session.add(row)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

def test_database_rejects_duplicate_fact_evidence_for_same_claim(client, db_session):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.models.claim_evidence import ClaimEvidence

    entity_id, claim_id = _setup_claim_and_entity(client)
    fact_id = create_financial_fact(client, entity_id).json()["id"]

    db_session.add(
        ClaimEvidence(claim_id=claim_id, financial_fact_id=fact_id, relationship_type="supports")
    )
    db_session.commit()

    db_session.add(
        ClaimEvidence(claim_id=claim_id, financial_fact_id=fact_id, relationship_type="context")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_rejects_duplicate_event_evidence_for_same_claim(client, db_session):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.models.claim_evidence import ClaimEvidence

    entity_id, claim_id = _setup_claim_and_entity(client)
    event_id = create_event(client, entity_id).json()["id"]

    db_session.add(
        ClaimEvidence(claim_id=claim_id, event_id=event_id, relationship_type="supports")
    )
    db_session.commit()

    db_session.add(
        ClaimEvidence(claim_id=claim_id, event_id=event_id, relationship_type="context")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_same_financial_fact_allowed_as_evidence_for_different_claims_db_level(client, db_session):
    from app.models.claim_evidence import ClaimEvidence

    entity_id = create_entity(client).json()["id"]
    case_id = create_research_case(client).json()["id"]
    claim_a = create_claim(client, case_id, statement="Claim A").json()["id"]
    claim_b = create_claim(client, case_id, statement="Claim B").json()["id"]
    fact_id = create_financial_fact(client, entity_id).json()["id"]

    db_session.add(
        ClaimEvidence(claim_id=claim_a, financial_fact_id=fact_id, relationship_type="supports")
    )
    db_session.commit()
    db_session.add(
        ClaimEvidence(claim_id=claim_b, financial_fact_id=fact_id, relationship_type="supports")
    )
    db_session.commit()  # should succeed - different claims, same fact is allowed
