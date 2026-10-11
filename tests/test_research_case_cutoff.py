from datetime import datetime, timedelta, timezone

from app.core.time_utils import to_naive_utc


def create_case(client, **overrides):
    payload = {"entity_id": None, "title": "Cutoff case", "description": "d", "status": "active"}
    payload.update(overrides)
    return client.post("/research-cases", json=payload)


# ---- to_naive_utc ----

def test_to_naive_utc_none():
    assert to_naive_utc(None) is None


def test_to_naive_utc_naive_is_taken_as_utc():
    assert to_naive_utc(datetime(2025, 1, 1, 10, 0)) == datetime(2025, 1, 1, 10, 0)


def test_to_naive_utc_converts_aware_to_utc():
    aware = datetime(2025, 1, 1, 10, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    result = to_naive_utc(aware)
    assert result == datetime(2025, 1, 1, 4, 30)
    assert result.tzinfo is None


def test_to_naive_utc_utc_aware():
    result = to_naive_utc(datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc))
    assert result == datetime(2025, 6, 1, 12, 0)
    assert result.tzinfo is None


# ---- create ----

def test_create_without_cutoff_returns_null(client):
    response = create_case(client)
    assert response.status_code == 200
    assert response.json()["knowledge_cutoff_at"] is None


def test_create_with_cutoff_round_trips(client):
    created = create_case(client, knowledge_cutoff_at="2025-03-01T09:30:00").json()
    assert created["knowledge_cutoff_at"] == "2025-03-01T09:30:00"
    fetched = client.get(f"/research-cases/{created['id']}").json()
    assert fetched["knowledge_cutoff_at"] == "2025-03-01T09:30:00"


def test_create_with_aware_offset_is_stored_as_naive_utc(client):
    created = create_case(client, knowledge_cutoff_at="2025-01-01T10:00:00+05:30").json()
    assert created["knowledge_cutoff_at"] == "2025-01-01T04:30:00"
    fetched = client.get(f"/research-cases/{created['id']}").json()
    assert fetched["knowledge_cutoff_at"] == "2025-01-01T04:30:00"


# ---- PATCH immutability ----

def test_patch_null_to_timestamp_rejected(client):
    case = create_case(client).json()
    response = client.patch(
        f"/research-cases/{case['id']}", json={"knowledge_cutoff_at": "2025-03-01T00:00:00"}
    )
    assert response.status_code == 422
    assert client.get(f"/research-cases/{case['id']}").json()["knowledge_cutoff_at"] is None


def test_patch_null_to_null_is_noop(client):
    case = create_case(client).json()
    response = client.patch(f"/research-cases/{case['id']}", json={"knowledge_cutoff_at": None})
    assert response.status_code == 200
    assert response.json()["knowledge_cutoff_at"] is None


def test_patch_existing_to_same_instant_is_noop(client):
    case = create_case(client, knowledge_cutoff_at="2025-03-01T00:00:00").json()
    response = client.patch(
        f"/research-cases/{case['id']}", json={"knowledge_cutoff_at": "2025-03-01T00:00:00"}
    )
    assert response.status_code == 200
    assert response.json()["knowledge_cutoff_at"] == "2025-03-01T00:00:00"


def test_patch_existing_to_same_instant_in_other_offset_is_noop(client):
    case = create_case(client, knowledge_cutoff_at="2025-03-01T00:00:00").json()
    response = client.patch(
        f"/research-cases/{case['id']}", json={"knowledge_cutoff_at": "2025-03-01T05:30:00+05:30"}
    )
    assert response.status_code == 200
    assert response.json()["knowledge_cutoff_at"] == "2025-03-01T00:00:00"


def test_patch_existing_to_different_instant_rejected(client):
    case = create_case(client, knowledge_cutoff_at="2025-03-01T00:00:00").json()
    response = client.patch(
        f"/research-cases/{case['id']}", json={"knowledge_cutoff_at": "2025-04-01T00:00:00"}
    )
    assert response.status_code == 422
    assert client.get(f"/research-cases/{case['id']}").json()["knowledge_cutoff_at"] == "2025-03-01T00:00:00"


def test_patch_existing_to_null_rejected(client):
    case = create_case(client, knowledge_cutoff_at="2025-03-01T00:00:00").json()
    response = client.patch(f"/research-cases/{case['id']}", json={"knowledge_cutoff_at": None})
    assert response.status_code == 422
    assert client.get(f"/research-cases/{case['id']}").json()["knowledge_cutoff_at"] == "2025-03-01T00:00:00"


def test_patch_omitting_cutoff_is_noop(client):
    case = create_case(client, knowledge_cutoff_at="2025-03-01T00:00:00").json()
    response = client.patch(f"/research-cases/{case['id']}", json={"title": "Renamed"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Renamed"
    assert data["knowledge_cutoff_at"] == "2025-03-01T00:00:00"


def test_rejected_cutoff_patch_applies_no_other_fields(client):
    case = create_case(client, knowledge_cutoff_at="2025-03-01T00:00:00").json()
    response = client.patch(
        f"/research-cases/{case['id']}",
        json={"title": "Should not apply", "knowledge_cutoff_at": "2025-04-01T00:00:00"},
    )
    assert response.status_code == 422
    assert client.get(f"/research-cases/{case['id']}").json()["title"] == "Cutoff case"


def test_other_patch_fields_still_work(client):
    case = create_case(client).json()
    response = client.patch(
        f"/research-cases/{case['id']}",
        json={"title": "New title", "description": "New description", "status": "archived"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New title"
    assert data["description"] == "New description"
    assert data["status"] == "archived"


def test_patch_missing_case_returns_404(client):
    assert client.patch("/research-cases/999999", json={"title": "x"}).status_code == 404
