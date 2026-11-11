import importlib
import sys

import pytest
from fastapi.testclient import TestClient


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GATEWAY_SUBTITLES_URL", "http://subtitles.test")
    monkeypatch.setenv("GATEWAY_SUBTITLES_TIMEOUT_SECONDS", "1.0")
    _purge_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client
