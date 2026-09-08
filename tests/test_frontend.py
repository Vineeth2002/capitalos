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