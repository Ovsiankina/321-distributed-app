import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app import proxy as proxy_module

_KEY = Ed25519PrivateKey.generate()


def _pem() -> str:
    return _KEY.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()


class _Stream:
    def __init__(self, captured, method, url, headers, content):
        captured.update(method=method, url=url, headers=headers or {}, content=content)
        self.status_code = 200
        self.headers = {"content-type": "application/json"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def aread(self):
        return b'{"items":[]}'


class _Client:
    def __init__(self, captured):
        self.captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def stream(self, method, url, headers=None, content=None):
        return _Stream(self.captured, method, url, headers, content)


def test_v2_catalog_strips_version_and_ignores_client_identity(client, monkeypatch):
    captured = {}

    def factory(**_kwargs):
        return _Client(captured)

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", factory)
    response = client.get(
        "/api/v2/catalog/videos",
        headers={"X-User-Id": "1", "X-Channel-Id": "spoof"},
    )
    assert response.status_code == 200
    assert captured["url"] == "http://catalog.test/api/catalog/videos"
    assert "x-user-id" not in {name.lower() for name in captured["headers"]}
    assert captured["headers"]["x-forwarded-prefix"] == "/api/v2"


def test_v2_upload_requires_jwt(client):
    response = client.post("/api/v2/upload/videos")
    assert response.status_code == 401


def test_v2_unknown_route(client):
    response = client.get("/api/v2/subtitles/fr")
    assert response.status_code == 404


def test_v1_catalog_is_marked_deprecated(client, monkeypatch):
    class Broken:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def request(self, *_args, **_kwargs):
            raise httpx.ConnectError("down")

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", lambda **_kw: Broken())
    response = client.get("/api/catalog/videos")
    assert response.status_code == 502
    assert response.headers.get("deprecation") == "true"
