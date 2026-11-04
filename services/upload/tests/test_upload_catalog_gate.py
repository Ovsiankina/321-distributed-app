from fastapi import HTTPException

UPLOAD_PATH = "/api/upload/videos"
SAMPLE_FILE = ("clip.mp4", b"fake", "video/mp4")


def test_upload_returns_503_when_catalog_not_ready(client, auth_headers, monkeypatch):
    def catalog_down() -> None:
        raise HTTPException(status_code=503, detail="Catalog indisponible")

    monkeypatch.setattr("app.catalog_client.ensure_catalog_ready", catalog_down)

    response = client.post(
        UPLOAD_PATH,
        headers=auth_headers,
        files={"file": SAMPLE_FILE},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Catalog indisponible"}


def test_upload_without_token_does_not_require_catalog(client, monkeypatch):
    calls = 0

    def catalog_down() -> None:
        nonlocal calls
        calls += 1
        raise HTTPException(status_code=503, detail="Catalog indisponible")

    monkeypatch.setattr("app.catalog_client.ensure_catalog_ready", catalog_down)

    response = client.post(UPLOAD_PATH, files={"file": SAMPLE_FILE})
    assert response.status_code == 401
    assert calls == 0
