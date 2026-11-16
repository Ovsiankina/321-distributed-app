import pytest


@pytest.mark.parametrize(
    "path", ["/api/auth/favorites", "/api/auth/favorites/abc", "/inconnu"]
)
def test_unknown_route_answers_in_french(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert response.json() == {"detail": "Route inconnue"}


def test_wrong_method_answers_in_french(client):
    response = client.get("/api/auth/register")
    assert response.status_code == 405
    assert response.json() == {"detail": "Méthode non autorisée"}
    assert response.headers["Allow"] == "POST"


def test_route_details_and_headers_pass_through(client):
    body = {"email": "a@example.com", "password": "mauvais"}
    for _ in range(10):
        client.post("/api/auth/login", json=body)
    response = client.post("/api/auth/login", json=body)
    assert response.json() == {"detail": "Trop de tentatives, réessayez plus tard"}
    assert "Retry-After" in response.headers
