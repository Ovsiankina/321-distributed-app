import httpx

from app import proxy as proxy_module


def test_auth_proxy_returns_502_when_upstream_down(client, monkeypatch):
    class BrokenClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def request(self, *_args, **_kwargs):
            raise httpx.ConnectError("down")

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", lambda **_kw: BrokenClient())

    response = client.get("/api/auth/me")
    assert response.status_code == 502
    assert response.json() == {"detail": "Service indisponible"}


def test_auth_proxy_forwards_get_with_authorization(client, monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        content = b'{"id":"user-1"}'
        headers = {"content-type": "application/json"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def request(self, method, url, headers=None, content=None):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers or {}
            return FakeResponse()

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", lambda **_kw: FakeClient())

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer token"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": "user-1"}
    assert captured["method"] == "GET"
    assert captured["url"] == "http://auth.test/api/auth/me"
    assert captured["headers"]["authorization"] == "Bearer token"


def test_auth_proxy_forwards_post_login(client, monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        content = b'{"token":"jwt"}'
        headers = {"content-type": "application/json"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def request(self, method, url, headers=None, content=None):
            captured["method"] = method
            captured["url"] = url
            captured["content"] = content
            return FakeResponse()

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", lambda **_kw: FakeClient())

    response = client.post(
        "/api/auth/login",
        headers={"Content-Type": "application/json"},
        json={"email": "a@b.c", "password": "secret"},
    )
    assert response.status_code == 200
    assert captured["method"] == "POST"
    assert captured["url"] == "http://auth.test/api/auth/login"
    assert captured["content"] is not None
