import pytest
from sqlalchemy.exc import IntegrityError

from app.models.claim_evidence import ClaimEvidence
from app.schemas.claim_evidence import ClaimEvidenceCreate
from app.services.claim_evidence_service import ClaimEvidenceError, attach_evidence


def make_entity(client, name="Integrity Co"):
    return client.post(
        "/entities",
        json={
            "entity_type": "company",
            "canonical_name": name,
            "ticker": None,
            "exchange": None,
            "status": "active",
        },
    ).json()["id"]


def make_case(client):
    return client.post(
        "/research-cases",
        json={"entity_id": None, "title": "Integrity case", "description": None, "status": "active"},
    ).json()["id"]


def make_claim(client, case_id, statement="Integrity claim"):
    return client.post(
        f"/research-cases/{case_id}/claims",
        json={
            "entity_id": None,
            "statement": statement,
            "temporal_orientation": "current",
            "epistemic_role": "interpretation",
            "shape": "qualitative",
            "confidence_band": None,
            "lifecycle_status": "active",
            "lens": None,
            "origin": "user",
        },
    ).json()["id"]


def make_fact(client, entity_id):
    return client.post(
        "/financial-facts",
        json={"entity_id": entity_id, "fact_type": "revenue", "value_numeric": "100"},
    ).json()["id"]


def make_event(client, entity_id):
    return client.post(
        "/events",
        json={"entity_id": entity_id, "event_type": "leadership_change", "description": "CEO resigned"},
    ).json()["id"]


# ---- database-level invariants ----

def test_db_rejects_evidence_with_no_subject(client, db_session):
    claim_id = make_claim(client, make_case(client))
    db_session.add(ClaimEvidence(claim_id=claim_id, relationship_type="supports"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_db_rejects_evidence_with_both_subjects(client, db_session):
    entity_id = make_entity(client)
    claim_id = make_claim(client, make_case(client))
    db_session.add(
        ClaimEvidence(
            claim_id=claim_id,
            financial_fact_id=make_fact(client, entity_id),
            event_id=make_event(client, entity_id),
            relationship_type="supports",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_db_rejects_duplicate_fact_for_same_claim(client, db_session):
    entity_id = make_entity(client)
    claim_id = make_claim(client, make_case(client))
    fact_id = make_fact(client, entity_id)

    db_session.add(ClaimEvidence(claim_id=claim_id, financial_fact_id=fact_id, relationship_type="supports"))
    db_session.commit()
    db_session.add(ClaimEvidence(claim_id=claim_id, financial_fact_id=fact_id, relationship_type="context"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_db_rejects_duplicate_event_for_same_claim(client, db_session):
    entity_id = make_entity(client)
    claim_id = make_claim(client, make_case(client))
    event_id = make_event(client, entity_id)

    db_session.add(ClaimEvidence(claim_id=claim_id, event_id=event_id, relationship_type="supports"))
    db_session.commit()
    db_session.add(ClaimEvidence(claim_id=claim_id, event_id=event_id, relationship_type="context"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_db_allows_same_fact_across_different_claims(client, db_session):
    entity_id = make_entity(client)
    case_id = make_case(client)
    claim_a = make_claim(client, case_id, "Claim A")
    claim_b = make_claim(client, case_id, "Claim B")
    fact_id = make_fact(client, entity_id)

    db_session.add(ClaimEvidence(claim_id=claim_a, financial_fact_id=fact_id, relationship_type="supports"))
    db_session.commit()
    db_session.add(ClaimEvidence(claim_id=claim_b, financial_fact_id=fact_id, relationship_type="supports"))
    db_session.commit()


def test_db_allows_same_event_across_different_claims(client, db_session):
    entity_id = make_entity(client)
    case_id = make_case(client)
    claim_a = make_claim(client, case_id, "Claim A")
    claim_b = make_claim(client, case_id, "Claim B")
    event_id = make_event(client, entity_id)

    db_session.add(ClaimEvidence(claim_id=claim_a, event_id=event_id, relationship_type="supports"))
    db_session.commit()
    db_session.add(ClaimEvidence(claim_id=claim_b, event_id=event_id, relationship_type="supports"))
    db_session.commit()


def test_db_allows_one_claim_to_cite_several_different_events(client, db_session):
    entity_id = make_entity(client)
    claim_id = make_claim(client, make_case(client))

    db_session.add(ClaimEvidence(claim_id=claim_id, event_id=make_event(client, entity_id), relationship_type="supports"))
    db_session.commit()
    db_session.add(ClaimEvidence(claim_id=claim_id, event_id=make_event(client, entity_id), relationship_type="context"))
    db_session.commit()


# ---- constraint-name mapping in the race-condition path ----

class _StubDiag:
    def __init__(self, constraint_name):
        self.constraint_name = constraint_name


class _StubDriverError(Exception):
    def __init__(self, constraint_name):
        super().__init__("stub driver error")
        self.diag = _StubDiag(constraint_name)


def _integrity_error(constraint_name):
    return IntegrityError("INSERT INTO claim_evidence ...", {}, _StubDriverError(constraint_name))


def _setup_for_attach(client):
    entity_id = make_entity(client)
    claim_id = make_claim(client, make_case(client))
    fact_id = make_fact(client, entity_id)
    return claim_id, fact_id


@pytest.mark.parametrize("constraint_name", ["uq_claim_evidence_fact", "uq_claim_evidence_event"])
def test_duplicate_index_violation_maps_to_409(client, db_session, monkeypatch, constraint_name):
    claim_id, fact_id = _setup_for_attach(client)

    def failing_commit():
        raise _integrity_error(constraint_name)

    monkeypatch.setattr(db_session, "commit", failing_commit)

    evidence_in = ClaimEvidenceCreate(financial_fact_id=fact_id, relationship_type="supports")
    with pytest.raises(ClaimEvidenceError) as exc_info:
        attach_evidence(db_session, claim_id, evidence_in)
    assert exc_info.value.status_code == 409


def test_unrelated_integrity_error_is_reraised_unchanged(client, db_session, monkeypatch):
    claim_id, fact_id = _setup_for_attach(client)
    original = _integrity_error("some_other_constraint")

    def failing_commit():
        raise original

    monkeypatch.setattr(db_session, "commit", failing_commit)

    evidence_in = ClaimEvidenceCreate(financial_fact_id=fact_id, relationship_type="supports")
    with pytest.raises(IntegrityError) as exc_info:
        attach_evidence(db_session, claim_id, evidence_in)
    assert exc_info.value is original


def test_integrity_error_without_diagnostics_is_reraised(client, db_session, monkeypatch):
    claim_id, fact_id = _setup_for_attach(client)
    original = IntegrityError("INSERT ...", {}, Exception("no diag attribute"))

    def failing_commit():
        raise original

    monkeypatch.setattr(db_session, "commit", failing_commit)

    evidence_in = ClaimEvidenceCreate(financial_fact_id=fact_id, relationship_type="supports")
    with pytest.raises(IntegrityError):
        attach_evidence(db_session, claim_id, evidence_in)


# ---- claim deletion with attached evidence ----

def test_claim_with_fact_evidence_cannot_be_deleted(client):
    entity_id = make_entity(client)
    claim_id = make_claim(client, make_case(client))
    fact_id = make_fact(client, entity_id)
    client.post(
        f"/claims/{claim_id}/evidence",
        json={"financial_fact_id": fact_id, "relationship_type": "supports"},
    )

    response = client.delete(f"/claims/{claim_id}")
    assert response.status_code == 409
    assert client.get(f"/claims/{claim_id}").status_code == 200


def test_claim_with_event_evidence_cannot_be_deleted(client):
    entity_id = make_entity(client)
    claim_id = make_claim(client, make_case(client))
    event_id = make_event(client, entity_id)
    client.post(
        f"/claims/{claim_id}/evidence",
        json={"event_id": event_id, "relationship_type": "context"},
    )

    assert client.delete(f"/claims/{claim_id}").status_code == 409
    assert client.get(f"/claims/{claim_id}").status_code == 200


def test_claim_deletable_after_evidence_is_detached(client):
    entity_id = make_entity(client)
    claim_id = make_claim(client, make_case(client))
    fact_id = make_fact(client, entity_id)
    evidence = client.post(
        f"/claims/{claim_id}/evidence",
        json={"financial_fact_id": fact_id, "relationship_type": "supports"},
    ).json()

    assert client.delete(f"/claims/{claim_id}/evidence/{evidence['id']}").status_code == 204
    assert client.delete(f"/claims/{claim_id}").status_code == 204