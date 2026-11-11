"""URLs des microservices pour les scénarios multi-services (variables d'environnement)."""

from __future__ import annotations

import os

import httpx
import pytest


def _base(name: str, default: str = "") -> str:
    return os.environ.get(name, default).rstrip("/")


def require_auth_url() -> str:
    url = _base("INTEGRATION_AUTH_URL")
    if not url:
        pytest.skip(
            "Service auth absent : définir INTEGRATION_AUTH_URL "
            "(JWT register/login/me/favorites)"
        )
    return url


def require_upload_url() -> str:
    url = _base("INTEGRATION_UPLOAD_URL")
    if not url:
        pytest.skip(
            "Service upload absent ou non spécifié dans gateway.openapi.yaml : "
            "définir INTEGRATION_UPLOAD_URL"
        )
    return url


def catalog_url() -> str:
    return _base("INTEGRATION_CATALOG_URL", "http://127.0.0.1:8002")


@pytest.fixture
def auth_http() -> httpx.Client:
    return httpx.Client(base_url=require_auth_url(), timeout=30.0)


@pytest.fixture
def catalog_http() -> httpx.Client:
    return httpx.Client(base_url=catalog_url(), timeout=30.0)


@pytest.fixture
def upload_http() -> httpx.Client:
    return httpx.Client(base_url=require_upload_url(), timeout=60.0)


def register_and_login(client: httpx.Client) -> str:
    import uuid

    email = f"integration-{uuid.uuid4().hex[:12]}@example.test"
    password = "integration-secret-12"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert reg.status_code in (201, 409), reg.text
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    body = login.json()
    token = body.get("access_token") or body.get("token")
    assert token, f"JWT attendu dans la réponse login : {body}"
    return token
