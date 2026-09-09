def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "CapitalOS" in response.text
    assert "Analyze My Reasoning" in response.text

def test_static_files_are_served(client):
    response = client.get("/static/app.js")
    assert response.status_code == 200

    response = client.get("/static/style.css")
    assert response.status_code == 200

def test_cases_list_page_loads(client):
    response = client.get("/cases")
    assert response.status_code == 200
    assert "Research Cases" in response.text

def test_workspace_page_loads_for_existing_case(client):
    create_response = client.post(
        "/research-cases",
        json={
            "entity_id": None,
            "title": "Workspace test case",
            "description": "Testing the workspace view",
            "status": "active",
        },
    )
    case_id = create_response.json()["id"]

    response = client.get("/cases/" + str(case_id))
    assert response.status_code == 200
    assert "CapitalOS" in response.text

def test_index_links_to_cases_list(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "/cases" in response.text
