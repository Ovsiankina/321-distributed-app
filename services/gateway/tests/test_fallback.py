def test_unknown_api_route(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 404
    assert response.json() == {"detail": "Route inconnue"}


def test_stream_not_proxied_yet(client):
    response = client.get("/api/stream/intro-streaming")
    assert response.status_code == 404
    assert response.json() == {"detail": "Route inconnue"}
