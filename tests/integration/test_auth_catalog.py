"""
Auth ↔ catalog : favoris liés à des video_id présents au catalog (contrat gateway E1-05).

Le catalog ne valide pas les JWT ; le couplage est côté service auth (404 si vidéo inconnue).
"""

from __future__ import annotations

import httpx
import pytest

from http_env import auth_http, catalog_http, register_and_login

pytestmark = pytest.mark.integration


def _skip_if_catalog_down(catalog_http: httpx.Client) -> None:
    try:
        health = catalog_http.get("/health")
    except httpx.HTTPError as exc:
        pytest.skip(f"Catalog injoignable sur {catalog_http.base_url} : {exc}")
    if health.status_code != 200:
        pytest.skip(f"Catalog injoignable sur {catalog_http.base_url} : {health.status_code}")


def test_catalog_reachable_for_auth_scenarios(catalog_http: httpx.Client):
    _skip_if_catalog_down(catalog_http)
    videos = catalog_http.get("/api/catalog/videos")
    assert videos.status_code == 200
    assert videos.json()["total"] >= 1


def test_add_favorite_on_existing_catalog_video(auth_http: httpx.Client, catalog_http: httpx.Client):
    _skip_if_catalog_down(catalog_http)
    token = register_and_login(auth_http)
    video_id = catalog_http.get("/api/catalog/videos").json()["items"][0]["id"]
    response = auth_http.post(
        f"/api/auth/favorites/{video_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text


def test_add_favorite_unknown_video_returns_404(auth_http: httpx.Client):
    token = register_and_login(auth_http)
    response = auth_http.post(
        "/api/auth/favorites/video-id-inexistant-integration",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404, response.text


def test_list_favorites_includes_catalog_metadata(auth_http: httpx.Client, catalog_http: httpx.Client):
    _skip_if_catalog_down(catalog_http)
    token = register_and_login(auth_http)
    video_id = catalog_http.get("/api/catalog/videos").json()["items"][0]["id"]
    auth_http.post(
        f"/api/auth/favorites/{video_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    listed = auth_http.get(
        "/api/auth/favorites",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert video_id in body.get("video_ids", [])
    videos = body.get("videos") or []
    assert any(v.get("id") == video_id for v in videos)
