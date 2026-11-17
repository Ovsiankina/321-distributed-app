import inspect
import time

import jwt

from conftest import AUDIENCE, ISSUER

from app.routers.upload import upload_video

UPLOAD_PATH = "/api/upload/videos"
SAMPLE_FILE = ("clip.mp4", b"fake", "video/mp4")


def test_upload_video_handler_is_sync():
    assert not inspect.iscoroutinefunction(upload_video)


def test_upload_without_token_returns_401(client):
    response = client.post(UPLOAD_PATH, files={"file": SAMPLE_FILE})
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentification requise"}


def test_upload_with_invalid_token_returns_401(client):
    response = client.post(
        UPLOAD_PATH,
        headers={"Authorization": "Bearer not-a-valid-jwt"},
        files={"file": SAMPLE_FILE},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentification requise"}


def test_upload_rejects_hs256_token(client):
    now = int(time.time())
    legacy = jwt.encode(
        {"sub": "1", "exp": now + 3600, "iss": ISSUER, "aud": AUDIENCE},
        "shared-secret",
        algorithm="HS256",
    )
    response = client.post(
        UPLOAD_PATH,
        headers={"Authorization": f"Bearer {legacy}"},
        files={"file": SAMPLE_FILE},
    )
    assert response.status_code == 401


def test_upload_with_valid_token_is_not_unauthorized(client, auth_headers):
    response = client.post(
        UPLOAD_PATH,
        headers=auth_headers,
        files={"file": SAMPLE_FILE},
    )
    assert response.status_code == 501
