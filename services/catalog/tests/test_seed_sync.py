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


def test_sqlite_sync_lock_does_not_block(client):
    from app.db import SessionLocal
    from app.seed import catalog_sync_lock

    db = SessionLocal()
    try:
        with catalog_sync_lock(db, blocking=False):
            with catalog_sync_lock(db, blocking=False):
                held = True
        assert held
    finally:
        db.close()


def test_database_lock_uses_get_lock_and_releases_it():
    from app.seed import catalog_sync_lock

    statements: list[str] = []

    class Result:
        def scalar(self):
            return 1

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def close(self):
            statements.append("close")

        def execute(self, statement, params=None):
            statements.append(str(statement))
            if params is not None:
                statements.append(str(params["timeout"]))
            return Result()

    class Bind:
        class dialect:
            name = "mysql"

        def connect(self):
            return Connection()

    class FakeSession:
        def get_bind(self):
            return Bind()

    with catalog_sync_lock(FakeSession()):
        pass
    assert "GET_LOCK" in statements[0]
    assert "30" in statements
    assert any("RELEASE_LOCK" in statement for statement in statements)


def test_database_lock_refuses_when_already_held():
    from app.seed import catalog_sync_lock

    class Result:
        def scalar(self):
            return 0

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def close(self):
            return None

        def execute(self, statement, params=None):
            return Result()

    class Bind:
        class dialect:
            name = "mariadb"

        def connect(self):
            return Connection()

    class FakeSession:
        def get_bind(self):
            return Bind()

    try:
        with catalog_sync_lock(FakeSession(), blocking=False):
            refused = False
    except BlockingIOError:
        refused = True
    assert refused
