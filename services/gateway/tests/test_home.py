def test_home_stub(client):
    response = client.get("/api/home")
    assert response.status_code == 200
    assert response.json() == {"sections": []}
