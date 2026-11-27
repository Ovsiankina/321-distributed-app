"""Client FastAPI catalog avec une URL de base de données donnée (rechargement module app)."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_ROOT = REPO_ROOT / "services" / "catalog"
FULL_FIXTURES = CATALOG_ROOT / "fixtures"


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


def build_catalog_test_client(
    tmp_path: Path,
    database_url: str,
    fixtures_dir: Path = FULL_FIXTURES,
) -> TestClient:
    sys.path.insert(0, str(CATALOG_ROOT))
    os.environ["CATALOG_FIXTURES_DIR"] = str(fixtures_dir)
    os.environ["CATALOG_DATABASE_URL"] = database_url
    os.environ.pop("CATALOG_DB_PASSWORD", None)
    os.environ.pop("CATALOG_VIDEOS_DIR", None)
    os.environ.pop("CATALOG_SUBTITLES_DIR", None)
    os.environ.pop("CATALOG_DATA_DIR", None)

    _purge_app_modules()
    main = importlib.import_module("app.main")
    return TestClient(main.app)
