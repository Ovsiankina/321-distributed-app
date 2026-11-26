"""Le service média n'accepte que l'identité posée par la Gateway (R7)."""

from __future__ import annotations

import httpx
import pytest

from http_env import upload_http

pytestmark = pytest.mark.integration

UPLOAD_PATH = "/api/upload/videos"


def test_upload_without_identity_is_rejected(upload_http: httpx.Client):
    response = upload_http.post(
        UPLOAD_PATH,
        files={"file": ("clip.mp4", b"fake", "video/mp4")},
        data={"title": "Demo"},
    )
    assert response.status_code == 401, response.text


def test_upload_with_creator_headers_is_not_unauthorized(upload_http: httpx.Client):
    response = upload_http.post(
        UPLOAD_PATH,
        headers={"X-User-Id": "1", "X-Channel-Id": "UC-demo"},
        files={"file": ("clip.mp4", b"fake", "video/mp4")},
        data={"title": "Demo"},
    )
    assert response.status_code != 401, response.text
