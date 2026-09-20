def test_create_event_creates_session_and_event(client):
    response = client.post(
        "/research-events",
        json={
            "session_id": "sess-test-1",
            "event_type": "REASONING_SUBMITTED",
            "payload": {"text": "hello"}
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == "sess-test-1"
    assert data["event_type"] == "REASONING_SUBMITTED"
    assert data["payload"] == {"text": "hello"}


def test_repeated_events_reuse_same_session(client):
    client.post(
        "/research-events",
        json={"session_id": "sess-test-2", "event_type": "A", "payload": {}}
    )
    client.post(
        "/research-events",
        json={"session_id": "sess-test-2", "event_type": "B", "payload": {}}
    )

    response = client.get("/research-events", params={"session_id": "sess-test-2"})
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2
    assert events[0]["event_type"] == "A"
    assert events[1]["event_type"] == "B"


def test_events_returned_in_chronological_order(client):
    for i in range(5):
        client.post(
            "/research-events",
            json={"session_id": "sess-test-3", "event_type": "EVENT_" + str(i), "payload": {}}
        )

    response = client.get("/research-events", params={"session_id": "sess-test-3"})
    events = response.json()
    event_types = [e["event_type"] for e in events]
    assert event_types == ["EVENT_0", "EVENT_1", "EVENT_2", "EVENT_3", "EVENT_4"]


def test_get_events_for_nonexistent_session_returns_404(client):
    response = client.get("/research-events", params={"session_id": "sess-does-not-exist"})
    assert response.status_code == 404


def test_existing_frontend_pages_still_load(client):
    response = client.get("/")
    assert response.status_code == 200
    response = client.get("/cases")
    assert response.status_code == 200