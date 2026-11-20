import importlib
import sys
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

SIGNING_KEY = Ed25519PrivateKey.generate()
ISSUER = "stream321-auth"
AUDIENCE = "stream321-api"


def public_key_pem(key: Ed25519PrivateKey = SIGNING_KEY) -> str:
    return key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DATA_DIR", str(tmp_path / "incoming"))
    monkeypatch.setenv("UPLOAD_JWT_PUBLIC_KEY", public_key_pem())
    monkeypatch.setenv("UPLOAD_CATALOG_URL", "http://catalog.test")

    _purge_app_modules()
    main = importlib.import_module("app.main")
    # La route lie le nom à l'import : patcher le module source ne suffit pas.
    monkeypatch.setattr(
        "app.routers.upload.ensure_catalog_ready",
        lambda: None,
    )
    with TestClient(main.app) as test_client:
        yield test_client


def mint_test_token(sub: str = "1") -> str:
    now = int(time.time())
    payload = {
        "iss": ISSUER,
        "sub": str(sub),
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(payload, SIGNING_KEY, algorithm="EdDSA")


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_test_token()}"}