"""
Upload ↔ Auth : l'upload doit refuser les requêtes non authentifiées.

L'API upload n'est pas encore dans docs/api/gateway.openapi.yaml ; ce fichier fixe
le scénario d'intégration à activer quand le contrat et le service existeront.
"""

from __future__ import annotations

import httpx
import pytest

from http_env import auth_http, upload_http

pytestmark = pytest.mark.integration

# Chemin provisoire : à aligner sur l'OpenAPI gateway quand la section upload sera stable.
UPLOAD_PATH = "/api/upload/videos"


def test_upload_without_token_is_rejected(upload_http: httpx.Client):
    response = upload_http.post(UPLOAD_PATH, files={"file": ("clip.mp4", b"fake", "video/mp4")})
    assert response.status_code == 401, response.text


def test_upload_with_valid_token_is_not_unauthorized(
    auth_http: httpx.Client,
    upload_http: httpx.Client,
):
    """Smoke : le JWT auth est accepté (201/400/415 acceptables, pas 401)."""
    from http_env import register_and_login

    token = register_and_login(auth_http)
    response = upload_http.post(
        UPLOAD_PATH,
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("clip.mp4", b"fake", "video/mp4")},
    )
    assert response.status_code != 401, response.text
