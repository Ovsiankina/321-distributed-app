def test_search_empty_query(client):
    response = client.get("/api/catalog/search", params={"q": ""})
    assert response.status_code == 200
    assert response.json() == {"items": [], "q": ""}


def test_search_whitespace_query(client):
    response = client.get("/api/catalog/search", params={"q": "   "})
    assert response.status_code == 200
    assert response.json() == {"items": [], "q": "   "}


def test_search_matches_title(client):
    response = client.get("/api/catalog/search", params={"q": "Internet"})
    assert response.status_code == 200
    body = response.json()
    assert body["q"] == "Internet"
    assert [item["id"] for item in body["items"]] == ["test-video-one"]


def test_search_matches_tag(client):
    response = client.get("/api/catalog/search", params={"q": "scrum"})
    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"]] == ["test-video-two"]
