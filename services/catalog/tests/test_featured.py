def test_featured_only_marked_videos(client):
    response = client.get("/api/catalog/featured")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == "test-video-one"
    assert items[0]["featured"] is True
