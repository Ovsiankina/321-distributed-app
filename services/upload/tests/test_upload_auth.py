UPLOAD_PATH = "/api/upload/videos"
SAMPLE = ("clip.mp4", b"\x00\x00\x00\x18ftyp", "video/mp4")


def test_upload_without_identity_returns_401(client):
    response = client.post(UPLOAD_PATH, files={"file": SAMPLE}, data={"title": "Demo"})
    assert response.status_code == 401


def test_upload_without_channel_returns_403(client):
    response = client.post(
        UPLOAD_PATH,
        headers={"X-User-Id": "1"},
        files={"file": SAMPLE},
        data={"title": "Demo"},
    )
    assert response.status_code == 403


def test_upload_rejects_non_mp4(client, creator_headers):
    response = client.post(
        UPLOAD_PATH,
        headers=creator_headers,
        files={"file": ("clip.txt", b"hi", "text/plain")},
        data={"title": "Demo"},
    )
    assert response.status_code == 415


def test_upload_publishes_and_returns_202(client, creator_headers, monkeypatch):
    published = {}

    async def fake_publish(event_type, data):
        published["type"] = event_type
        published["data"] = data

    monkeypatch.setattr("app.routers.upload.probe_duration", lambda _path: 4)
    monkeypatch.setattr("app.routers.upload.make_thumbnail", lambda _path: b"\xff\xd8\xff\xd9")
    monkeypatch.setattr("app.routers.upload.messaging.publish_event", fake_publish)

    response = client.post(
        UPLOAD_PATH,
        headers=creator_headers,
        files={"file": SAMPLE},
        data={"title": "Demo", "tags": "a, b"},
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "processing"
    assert published["type"] == "video.uploaded"
    assert published["data"]["channel_id"] == "UC-demo"
    assert published["data"]["tags"] == ["a", "b"]
