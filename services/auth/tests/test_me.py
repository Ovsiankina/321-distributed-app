import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from conftest import bearer, decode, mint, register
from gateway_openapi import assert_matches_gateway_schema

ME_PATH = "/api/auth/me"
UNAUTHORIZED = {"detail": "Authentification requise"}


def test_me_returns_the_current_user(client):
    token = register(client).json()["token"]
    response = client.get(ME_PATH, headers=bearer(token))
    assert response.status_code == 200
    assert response.json() == {
        "id": int(decode(token)["sub"]),
        "email": "alice@example.com",
    }
    assert_matches_gateway_schema(response.json(), ME_PATH)


def test_me_without_header_returns_401(client):
    response = client.get(ME_PATH)
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED
    assert_matches_gateway_schema(response.json(), ME_PATH, status="401")


def test_me_with_another_scheme_returns_401(client):
    token = register(client).json()["token"]
    response = client.get(ME_PATH, headers={"Authorization": f"Basic {token}"})
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED


def _tampered(token: str) -> str:
    header, payload, signature = token.split(".")
    other = mint(sub="2").split(".")[1]
    assert other != payload
    return f"{header}.{other}.{signature}"


def _unsigned() -> str:
    payload = mint().split(".")[1]
    none_header = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0"  # {"alg":"none","typ":"JWT"}
    return f"{none_header}.{payload}."


BAD_TOKENS = {
    "expiré depuis plus de 30 s": lambda: mint(exp=int(time.time()) - 31),
    "autre clé": lambda: mint(key=Ed25519PrivateKey.generate()),
    "autre émetteur": lambda: mint(iss="quelqu-un"),
    "autre audience": lambda: mint(aud="autre-api"),
    "sans exp": lambda: mint(exp=None),
    "sub non numérique": lambda: mint(sub="alice"),
    "payload modifié": lambda: _tampered(mint()),
    "alg none": _unsigned,
    "HS256": lambda: mint(key="clé-partagée-de-trente-deux-octets!", algorithm="HS256"),
    "pas un JWT": lambda: "abc.def",
}


@pytest.mark.parametrize("make_token", BAD_TOKENS.values(), ids=BAD_TOKENS.keys())
def test_invalid_token_returns_401(client, make_token):
    register(client)
    response = client.get(ME_PATH, headers=bearer(make_token()))
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED


def test_token_expired_within_the_clock_skew_is_accepted(client):
    user_id = decode(register(client).json()["token"])["sub"]
    token = mint(sub=user_id, exp=int(time.time()) - 10)
    assert client.get(ME_PATH, headers=bearer(token)).status_code == 200


def test_token_for_an_unknown_account_returns_401(client):
    response = client.get(ME_PATH, headers=bearer(mint(sub="999")))
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED
