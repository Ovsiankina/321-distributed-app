import importlib
import sys

import pytest
from fastapi.testclient import TestClient


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DATA_DIR", str(tmp_path / "videos"))
    _purge_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def creator_headers() -> dict[str, str]:
    return {"X-User-Id": "7", "X-Channel-Id": "UC-demo"}
