import httpx

from app.routers import subtitles as subtitles_router


def test_subtitles_proxy_returns_502_when_upstream_down(client, monkeypatch):
    class BrokenClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def request(self, *_args, **_kwargs):
            raise httpx.ConnectError("down")

    monkeypatch.setattr(
        subtitles_router.httpx, "AsyncClient", lambda **_kw: BrokenClient()
    )

    response = client.get("/api/subtitles/fr/foo.srt")
    assert response.status_code == 502
    assert response.json() == {"detail": "Service indisponible"}


def test_subtitles_proxy_forwards_get(client, monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        content = b"WEBVTT\n"
        headers = {"content-type": "text/vtt"}

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

    monkeypatch.setattr(subtitles_router.httpx, "AsyncClient", lambda **_kw: FakeClient())

    response = client.get(
        "/api/subtitles/videos/abc/fr",
        headers={"Authorization": "Bearer token"},
    )
    assert response.status_code == 200
    assert response.content == b"WEBVTT\n"
    assert captured["method"] == "GET"
    assert captured["url"] == "http://subtitles.test/api/subtitles/videos/abc/fr"
    assert captured["headers"]["authorization"] == "Bearer token"
