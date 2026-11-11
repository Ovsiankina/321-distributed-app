def test_video_detail_found(client):
    response = client.get("/api/catalog/videos/test-video-two")
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Daily Scrum bimensuel"
    assert "agile" in body["tags"]


def test_video_detail_not_found(client):
    response = client.get("/api/catalog/videos/missing-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Vidéo introuvable"}
