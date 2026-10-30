def test_full_catalog_has_ten_videos(full_client):
    response = full_client.get("/api/catalog/videos")
    assert response.status_code == 200
    assert response.json()["total"] == 10


def test_full_featured_count(full_client):
    response = full_client.get("/api/catalog/featured")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 4
