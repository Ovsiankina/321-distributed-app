import importlib
import sys
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

TEST_JWT_SECRET = "upload-test-jwt-secret"
TEST_JWT_ALGORITHM = "HS256"


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DATA_DIR", str(tmp_path / "incoming"))
    monkeypatch.setenv("UPLOAD_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("UPLOAD_JWT_ALGORITHM", TEST_JWT_ALGORITHM)
    monkeypatch.setenv("UPLOAD_CATALOG_URL", "http://catalog.test")

    _purge_app_modules()
    main = importlib.import_module("app.main")
    monkeypatch.setattr(
        "app.catalog_client.ensure_catalog_ready",
        lambda: None,
    )
    with TestClient(main.app) as test_client:
        yield test_client


def mint_test_token(sub: str = "user-1", email: str = "uploader@example.test") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "email": email,
        "exp": now + timedelta(hours=1),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_test_token()}"}
