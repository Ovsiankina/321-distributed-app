"""Garde-fous HTTP pour les scénarios qui supposent le catalog démarré."""

from __future__ import annotations

import httpx
import pytest


def skip_if_catalog_down(catalog_http: httpx.Client) -> None:
    try:
        health = catalog_http.get("/health")
    except httpx.HTTPError as exc:
        pytest.skip(f"Catalog injoignable sur {catalog_http.base_url} : {exc}")
    if health.status_code != 200:
        pytest.skip(f"Catalog injoignable sur {catalog_http.base_url} : {health.status_code}")
    body = health.json()
    if body.get("status") != "ok" or body.get("service") != "catalog":
        pytest.skip(
            f"Catalog /health inattendu sur {catalog_http.base_url} : {body}"
        )
