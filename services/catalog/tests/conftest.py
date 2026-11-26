import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TESTS_ROOT = Path(__file__).resolve().parent
SERVICE_ROOT = TESTS_ROOT.parent
MINI_FIXTURES = TESTS_ROOT / "fixtures"
FULL_FIXTURES = SERVICE_ROOT / "fixtures"


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


def _build_client(tmp_path: Path, fixtures_dir: Path) -> TestClient:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    import os

    os.environ["CATALOG_FIXTURES_DIR"] = str(fixtures_dir)
    os.environ["CATALOG_DATABASE_URL"] = f"sqlite:///{data_dir / 'test.db'}"
    os.environ.pop("CATALOG_DB_PASSWORD", None)

    _purge_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def client(tmp_path):
    yield from _build_client(tmp_path, MINI_FIXTURES)


@pytest.fixture
def full_client(tmp_path):
    yield from _build_client(tmp_path, FULL_FIXTURES)


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def thumb_jpeg(client):
    from app.db import SessionLocal
    from app.models import Video

    blob = b"\xff\xd8\xff\xd9"
    db = SessionLocal()
    try:
        row = db.get(Video, "test-video-one")
        row.thumbnail_jpeg = blob
        db.commit()
    finally:
        db.close()
    return blob
