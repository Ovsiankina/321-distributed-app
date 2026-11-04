"""
Upload ↔ Catalog : l'upload refuse de traiter une requête authentifiée si le catalog n'est pas ON.

Prérequis : catalog (8002) et upload (8003) démarrés ; upload configuré avec
UPLOAD_CATALOG_URL pointant vers le catalog. JWT via INTEGRATION_AUTH_URL si le test
avec token est exécuté.
"""

from __future__ import annotations

import pytest

from catalog_health import skip_if_catalog_down
from http_env import auth_http, catalog_http, register_and_login, upload_http

pytestmark = pytest.mark.integration

UPLOAD_PATH = "/api/upload/videos"
SAMPLE_FILE = ("clip.mp4", b"fake", "video/mp4")


def test_catalog_health_is_ok_for_upload_scenarios(catalog_http):
    skip_if_catalog_down(catalog_http)


def test_upload_with_valid_jwt_not_503_when_catalog_is_up(
    auth_http,
    catalog_http,
    upload_http,
):
    skip_if_catalog_down(catalog_http)
    token = register_and_login(auth_http)
    response = upload_http.post(
        UPLOAD_PATH,
        headers={"Authorization": f"Bearer {token}"},
        files={"file": SAMPLE_FILE},
    )
    assert response.status_code != 503, response.text
