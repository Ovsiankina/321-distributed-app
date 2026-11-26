import os
import select
import signal
import subprocess
import sys
from pathlib import Path


def test_sync_keeps_uploaded_rows_and_reports_removed_fixtures(client, tmp_path):
    import json

    from app.db import SessionLocal
    from app.models import Tag, Video
    from app.seed import sync_catalog_db

    db = SessionLocal()
    try:
        db.add(
            Video(
                id="uploaded-one",
                channel_id="UCX",
                title="Mine",
                description="",
                thumbnail_path="",
                duration_seconds=3,
                featured=False,
                qualities='["720p"]',
                subtitle_langs="[]",
                stream_modes='["mp4"]',
                subtitle_formats="[]",
                source="upload",
            )
        )
        db.flush()
        db.add(Tag(tag="demo", video_id="uploaded-one"))
        db.commit()

        catalog = tmp_path / "only-one.json"
        catalog.write_text(
            json.dumps(
                {
                    "videos": [
                        {
                            "id": "test-video-one",
                            "channel_id": "UC_test_channel_one",
                            "title": "Internet et réseaux",
                            "description": "Explication du fonctionnement d'Internet.",
                            "tags": ["internet"],
                            "duration_string": "26:02",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        featured = tmp_path / "featured.json"
        featured.write_text('{"video_ids": []}', encoding="utf-8")
        result = sync_catalog_db(db, catalog, featured)
        db.expire_all()

        kept = db.get(Video, "uploaded-one")
        assert kept is not None
        assert kept.title == "Mine"
        assert [row.tag for row in kept.tag_rows] == ["demo"]
        assert db.get(Video, "test-video-two") is None
        assert {item["video_id"] for item in result.removed} == {"test-video-two"}
    finally:
        db.close()


def test_startup_sync_refreshes_existing_rows(client):
    from app.db import SessionLocal
    from app.models import Video
    from app.seed import sync_catalog_on_startup

    db = SessionLocal()
    try:
        row = db.get(Video, "test-video-one")
        assert row is not None
        row.title = "titre local obsolete"
        db.commit()
        sync_catalog_on_startup(db)
        db.expire_all()
        assert db.get(Video, "test-video-one").title == "Internet et réseaux"
    finally:
        db.close()


def test_seed_module_has_no_seed_if_empty(client):
    import app.seed as seed

    assert not hasattr(seed, "seed_if_empty")


def test_startup_sync_lock_is_exclusive_across_processes(client):
    from app.seed import catalog_sync_lock

    service_root = str(Path(__file__).resolve().parents[1])
    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "from app.seed import catalog_sync_lock\n"
                "import time\n"
                "with catalog_sync_lock():\n"
                "    print('held', flush=True)\n"
                "    time.sleep(30)\n"
            ),
        ],
        cwd=service_root,
        env={**os.environ, "PYTHONPATH": service_root},
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        ready, _, _ = select.select([holder.stdout], [], [], 5)
        assert ready, holder.stderr
        assert holder.stdout.readline().strip() == "held"

        acquired = False

        def _alarm(_signum, _frame):
            raise TimeoutError("le verrou a bloqué au lieu de refuser")

        previous = signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(3)
        try:
            with catalog_sync_lock(blocking=False):
                acquired = True
        except BlockingIOError:
            acquired = False
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous)
        assert acquired is False
    finally:
        holder.kill()
        holder.wait(timeout=5)
