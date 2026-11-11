import httpx

from app import proxy as proxy_module


def test_catalog_proxy_returns_502_when_upstream_down(client, monkeypatch):
    class BrokenClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def request(self, *_args, **_kwargs):
            raise httpx.ConnectError("down")

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", lambda **_kw: BrokenClient())

    response = client.get("/api/catalog/videos")
    assert response.status_code == 502
    assert response.json() == {"detail": "Service indisponible"}


def test_catalog_proxy_forwards_json_list(client, monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        content = b'{"items":[],"total":0}'
        headers = {"content-type": "application/json"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def request(self, method, url, headers=None, content=None):
            captured["method"] = method
            captured["url"] = url
            return FakeResponse()

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", lambda **_kw: FakeClient())

    response = client.get("/api/catalog/videos")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}
    assert captured["method"] == "GET"
    assert captured["url"] == "http://catalog.test/api/catalog/videos"


def test_catalog_proxy_forwards_search_query(client, monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        content = b'{"items":[],"q":"foo"}'
        headers = {"content-type": "application/json"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def request(self, method, url, headers=None, content=None):
            captured["url"] = url
            return FakeResponse()

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", lambda **_kw: FakeClient())

    response = client.get("/api/catalog/search?q=foo")
    assert response.status_code == 200
    assert captured["url"] == "http://catalog.test/api/catalog/search?q=foo"
