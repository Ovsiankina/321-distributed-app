def test_list_videos_returns_seeded_items(client):
    response = client.get("/api/catalog/videos")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    ids = {item["id"] for item in body["items"]}
    assert ids == {"test-video-one", "test-video-two"}


def test_video_duration_parsed(client):
    response = client.get("/api/catalog/videos/test-video-one")
    assert response.status_code == 200
    assert response.json()["duration_seconds"] == 1562
