import subprocess


def test_ensure_thumbnail_bounds_ffmpeg(client, monkeypatch):
    from app.config import CATALOG_VIDEOS_DIR, FFMPEG_TIMEOUT_SECONDS
    from app.media import ensure_thumbnail, thumb_path

    video_id = "test-video-one"
    (CATALOG_VIDEOS_DIR / f"{video_id}.mp4").write_bytes(b"not-a-real-mp4")
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        thumb_path(video_id).write_bytes(b"\xff\xd8\xff\xd9")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("app.media.subprocess.run", fake_run)
    assert ensure_thumbnail(video_id) == thumb_path(video_id)
    assert seen["timeout"] == FFMPEG_TIMEOUT_SECONDS
    assert FFMPEG_TIMEOUT_SECONDS > 0


def test_ensure_thumbnail_timeout_drops_partial_file(client, monkeypatch):
    from app.config import CATALOG_VIDEOS_DIR
    from app.media import ensure_thumbnail, thumb_path

    video_id = "test-video-one"
    (CATALOG_VIDEOS_DIR / f"{video_id}.mp4").write_bytes(b"not-a-real-mp4")

    def fake_run(cmd, **kwargs):
        thumb_path(video_id).write_bytes(b"partial")
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 1))

    monkeypatch.setattr("app.media.subprocess.run", fake_run)
    assert ensure_thumbnail(video_id) is None
    assert not thumb_path(video_id).exists()