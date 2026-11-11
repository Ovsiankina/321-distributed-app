def test_thumbnail_missing_file(client):
    response = client.get("/api/catalog/videos/test-video-one/thumbnail")
    assert response.status_code == 404
    assert response.json() == {"detail": "Vidéo introuvable"}


def test_thumbnail_serves_jpeg(client, thumb_jpeg):
    response = client.get("/api/catalog/videos/test-video-one/thumbnail")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")
    assert response.content == thumb_jpeg.read_bytes()


def test_thumbnail_unknown_video(client):
    response = client.get("/api/catalog/videos/unknown/thumbnail")
    assert response.status_code == 404
