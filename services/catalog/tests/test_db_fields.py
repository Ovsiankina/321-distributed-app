def test_video_has_channel_id_and_thumbnail_path(client):
    from app.db import SessionLocal
    from app.models import Video

    db = SessionLocal()
    try:
        row = db.get(Video, "test-video-one")
        assert row is not None
        assert row.channel_id == "UC_test_channel_one"
        assert row.thumbnail_path == "thumbs/test-video-one.jpg"
    finally:
        db.close()
