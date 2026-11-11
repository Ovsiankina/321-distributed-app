def test_cors_wildcard_does_not_advertise_credentials(client):
    response = client.get("/health", headers={"Origin": "http://frontend.example"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers


def test_cors_preflight_wildcard_does_not_advertise_credentials(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://frontend.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers