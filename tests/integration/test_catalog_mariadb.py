"""Catalog persisté sur MariaDB (pas SQLite in-memory des tests unitaires)."""

import pytest
from fastapi.testclient import TestClient

from catalog_client import build_catalog_test_client

pytestmark = pytest.mark.integration


@pytest.fixture
def mariadb_client(tmp_path, integration_mariadb_url) -> TestClient:
    client = build_catalog_test_client(tmp_path, integration_mariadb_url)
    with client:
        yield client


def test_seed_persists_ten_videos_on_mariadb(mariadb_client):
    response = mariadb_client.get("/api/catalog/videos")
    assert response.status_code == 200
    assert response.json()["total"] == 10


def test_search_internet_on_mariadb(mariadb_client):
    response = mariadb_client.get("/api/catalog/search", params={"q": "internet"})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert "UXielWVovBo" in ids
