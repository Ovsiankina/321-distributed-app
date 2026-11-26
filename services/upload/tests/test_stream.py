def test_stream_missing_video_is_404(client):
    response = client.get("/api/stream/intro")
    assert response.status_code == 404


def test_stream_unknown_quality_is_400(client, tmp_path, monkeypatch):
    from app.config import data_dir

    folder = data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "intro.mp4").write_bytes(b"0123456789")
    response = client.get("/api/stream/intro?quality=4k")
    assert response.status_code == 400


def test_stream_range_returns_206(client):
    from app.config import data_dir

    folder = data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "intro.mp4").write_bytes(b"0123456789")
    response = client.get("/api/stream/intro", headers={"Range": "bytes=2-5"})
    assert response.status_code == 206
    assert response.content == b"2345"
    assert response.headers["content-range"] == "bytes 2-5/10"


def test_rejected_event_deletes_the_file(client):
    from app.config import data_dir
    from app.messaging import handle_rejected_payload
    from app.routers.upload import apply_rejection

    folder = data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "intro.mp4"
    target.write_bytes(b"mp4")
    apply_rejection("intro")
    assert not target.exists()
    target.write_bytes(b"mp4")
    handle_rejected_payload({"data": {"video_id": "intro", "reason": "invalid_metadata"}})
    assert not target.exists()
    handle_rejected_payload({"data": {"video_id": "intro", "reason": "invalid_metadata"}})
    other = folder / "other.mp4"
    other.write_bytes(b"stay")
    handle_rejected_payload({"data": {"video_id": "../other"}})
    assert other.exists()
