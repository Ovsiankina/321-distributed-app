import asyncio


def test_announce_publishes_one_dataset_message_per_safe_mp4(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DATA_DIR", str(tmp_path))
    (tmp_path / "intro.mp4").write_bytes(b"x")
    (tmp_path / "bad name.mp4").write_bytes(b"x")
    (tmp_path / "short.mp4").write_bytes(b"x")
    published = []

    async def fake_publish(event_type, data):
        published.append((event_type, data))

    def duration(path):
        return None if path.name == "short.mp4" else 8

    from app.announce import announce

    monkeypatch.setattr("app.announce.probe_duration", duration)
    monkeypatch.setattr("app.announce.make_thumbnail", lambda _path: b"\xff\xd8\xff")
    monkeypatch.setattr("app.announce.publish_event", fake_publish)

    assert asyncio.run(announce()) == 1
    event_type, data = published[0]
    assert event_type == "video.uploaded"
    assert data["origin"] == "dataset"
    assert data["video_id"] == "intro"
    assert data["duration_seconds"] == 8
    assert "title" not in data
