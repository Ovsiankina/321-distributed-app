import importlib
import sys
import time
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

TESTS_ROOT = Path(__file__).resolve().parent
MINI_FIXTURES = TESTS_ROOT / "fixtures"
FULL_FIXTURES = TESTS_ROOT.parent / "fixtures"

SIGNING_KEY = Ed25519PrivateKey.generate()
ISSUER = "stream321-auth"
AUDIENCE = "stream321-api"

SEEDED_EMAIL = "createur@stream321.local"
SEED_PASSWORD = "demo1234"


def private_key_pem(key) -> str:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


@pytest.fixture
def auth_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DATABASE_URL", f"sqlite:///{tmp_path / 'auth.db'}")
    monkeypatch.setenv("AUTH_JWT_PRIVATE_KEY", private_key_pem(SIGNING_KEY))
    monkeypatch.setenv("AUTH_FIXTURES_DIR", str(MINI_FIXTURES))
    for name in (
        "AUTH_DB_PASSWORD",
        "AUTH_JWT_ISSUER",
        "AUTH_JWT_AUDIENCE",
        "AUTH_TOKEN_TTL_HOURS",
    ):
        monkeypatch.delenv(name, raising=False)
    _purge_app_modules()
    yield
    # Chaque test réimporte app et crée un engine : fermer ses connexions SQLite avant
    # que pytest nettoie tmp_path (sous Windows, un fichier ouvert reste verrouillé).
    db = sys.modules.get("app.db")
    if db is not None:
        db.engine.dispose()


def _start_client():
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def client(auth_env):
    yield from _start_client()


@pytest.fixture
def full_client(auth_env, monkeypatch):
    monkeypatch.setenv("AUTH_FIXTURES_DIR", str(FULL_FIXTURES))
    yield from _start_client()


def register(client, email="alice@example.com", password="secret12"):
    return client.post(
        "/api/auth/register", json={"email": email, "password": password}
    )


def login(client, email="alice@example.com", password="secret12"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def decode(token: str) -> dict:
    return jwt.decode(
        token,
        SIGNING_KEY.public_key(),
        algorithms=["EdDSA"],
        issuer=ISSUER,
        audience=AUDIENCE,
    )


def mint(key=SIGNING_KEY, algorithm="EdDSA", **overrides) -> str:
    now = int(time.time())
    claims = {"iss": ISSUER, "sub": "1", "aud": AUDIENCE, "iat": now, "exp": now + 3600}
    claims.update(overrides)
    claims = {name: value for name, value in claims.items() if value is not None}
    return jwt.encode(claims, key, algorithm=algorithm)
