import importlib

import jwt
from fastapi.testclient import TestClient

from conftest import decode, register


def test_token_carries_only_the_documented_claims(client):
    token = register(client).json()["token"]
    claims = decode(token)
    assert set(claims) == {"iss", "sub", "aud", "iat", "exp"}
    assert claims["iss"] == "stream321-auth"
    assert claims["aud"] == "stream321-api"
    assert isinstance(claims["sub"], str)
    assert claims["exp"] - claims["iat"] == 3600


def test_token_header_is_eddsa(client):
    token = register(client).json()["token"]
    assert jwt.get_unverified_header(token) == {"alg": "EdDSA", "typ": "JWT"}


def test_lifetime_comes_from_the_environment(auth_env, monkeypatch):
    # La variable doit être posée avant l'import de l'application.
    monkeypatch.setenv("AUTH_TOKEN_TTL_HOURS", "24")
    main = importlib.import_module("app.main")
    with TestClient(main.app) as client:
        body = register(client).json()
    claims = decode(body["token"])
    assert body["expires_in_hours"] == 24
    assert claims["exp"] - claims["iat"] == 24 * 3600
