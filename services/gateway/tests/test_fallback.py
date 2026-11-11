def test_unknown_api_route(client):
    response = client.get("/api/catalog/videos")
    assert response.status_code == 404
    assert response.json() == {"detail": "Route inconnue"}
