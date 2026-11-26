import base64

JPEG = base64.b64encode(b"\xff\xd8\xff\xd9").decode()


def _ingest():
    from app.db import SessionLocal
    from app.events import ingest_uploaded

    return SessionLocal, ingest_uploaded


def test_invalid_upload_is_rejected(client):
    SessionLocal, ingest_uploaded = _ingest()
    published = []

    def publish(kind, data):
        published.append((kind, data))

    db = SessionLocal()
    try:
        status = ingest_uploaded(
            db,
            {
                "event_id": "evt-bad",
                "type": "video.uploaded",
                "data": {
                    "origin": "upload",
                    "video_id": "abc",
                    "title": "",
                    "channel_id": "UC",
                    "tags": [],
                    "duration_seconds": 2,
                    "thumbnail_jpeg_base64": JPEG,
                },
            },
            publish,
        )
    finally:
        db.close()
    assert status == "rejected"
    assert published == [("video.rejected", {"video_id": "abc", "reason": "invalid_metadata"})]


def test_upload_is_idempotent_and_visible(client):
    SessionLocal, ingest_uploaded = _ingest()
    published = []

    def publish(kind, data):
        published.append((kind, data))

    message = {
        "event_id": "evt-ok",
        "type": "video.uploaded",
        "data": {
            "origin": "upload",
            "video_id": "newvideo01",
            "title": "Demo",
            "channel_id": "UC1",
            "description": "x",
            "tags": ["demo"],
            "duration_seconds": 12,
            "qualities": ["720p"],
            "thumbnail_jpeg_base64": JPEG,
        },
    }
    db = SessionLocal()
    try:
        assert ingest_uploaded(db, message, publish) == "published"
        assert ingest_uploaded(db, message, publish) == "duplicate"
    finally:
        db.close()
    assert published[0][0] == "video.published"
    assert published[1][0] == "video.published"

    listed = client.get("/api/catalog/videos")
    ids = [item["id"] for item in listed.json()["items"]]
    assert "newvideo01" in ids


def test_dataset_thumbnail_updates_only_a_fixture_row(client):
    SessionLocal, ingest_uploaded = _ingest()
    published = []
    db = SessionLocal()
    try:
        status = ingest_uploaded(
            db,
            {
                "event_id": "evt-dataset",
                "type": "video.uploaded",
                "data": {
                    "origin": "dataset",
                    "video_id": "test-video-one",
                    "thumbnail_jpeg_base64": JPEG,
                },
            },
            lambda kind, data: published.append((kind, data)),
        )
        from app.models import Video

        row = db.get(Video, "test-video-one")
        assert status == "dataset"
        assert published == []
        assert row.thumbnail_jpeg == base64.b64decode(JPEG)
        assert row.title == "Internet et réseaux"
    finally:
        db.close()


def test_startup_messages_cover_remaining_and_removed_videos():
    from app.events import startup_messages
    from app.models import Video

    video = Video(id="kept", channel_id="UC1", title="Reste")
    messages = startup_messages(
        [video],
        [{"video_id": "gone", "channel_id": "UC2", "title": "Partie"}],
    )
    assert messages == [
        ("video.published", {"video_id": "kept", "channel_id": "UC1", "title": "Reste"}),
        ("video.removed", {"video_id": "gone", "channel_id": "UC2", "title": "Partie"}),
    ]


def test_thumbnail_url_uses_forwarded_prefix(client):
    response = client.get(
        "/api/catalog/videos/test-video-one",
        headers={"X-Forwarded-Prefix": "/api/v2"},
    )
    assert response.status_code == 200
    assert response.json()["thumbnail_url"].startswith("/api/v2/catalog/")
