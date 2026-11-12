import httpx

from app import proxy as proxy_module


def test_streaming_proxy_returns_502_when_upstream_down(client, monkeypatch):
    class BrokenClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def request(self, *_args, **_kwargs):
            raise httpx.ConnectError("down")

    monkeypatch.setattr(proxy_module.httpx, "AsyncClient", lambda **_kw: BrokenClient())

    response = client.get("/api/stream/intro-streaming")
    assert response.status_code == 502
    assert response.json() == {"detail": "Service indisponible"}


def test_streaming_proxy_forwards_get(client, monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        content = b"\x00\x00\x00\x18ftypmp42"
        headers = {"content-type": "video/mp4"}

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

    response = client.get("/api/stream/intro-streaming?quality=720p")
    assert response.status_code == 200
    assert response.content.startswith(b"\x00\x00\x00\x18")
    assert captured["method"] == "GET"
    assert (
        captured["url"]
        == "http://streaming.test/api/stream/intro-streaming?quality=720p"
    )
