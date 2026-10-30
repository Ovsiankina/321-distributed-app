"""Validation automatique des réponses catalog via le schéma OpenAPI gateway."""

from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

from gateway_openapi import GATEWAY_OPENAPI, assert_matches_gateway_schema


def test_gateway_openapi_document_is_valid():
    spec, _ = read_from_filename(str(GATEWAY_OPENAPI))
    validate(spec)


def test_list_videos_matches_gateway_schema(client):
    response = client.get("/api/catalog/videos")
    assert response.status_code == 200
    assert_matches_gateway_schema(response.json(), "/api/catalog/videos")


def test_featured_matches_gateway_schema(client):
    response = client.get("/api/catalog/featured")
    assert response.status_code == 200
    assert_matches_gateway_schema(response.json(), "/api/catalog/featured")


def test_search_matches_gateway_schema(client):
    response = client.get("/api/catalog/search", params={"q": "Internet"})
    assert response.status_code == 200
    assert_matches_gateway_schema(response.json(), "/api/catalog/search")


def test_video_detail_matches_gateway_schema(client):
    response = client.get("/api/catalog/videos/test-video-one")
    assert response.status_code == 200
    assert_matches_gateway_schema(response.json(), "/api/catalog/videos/{video_id}")


def test_full_catalog_list_matches_gateway_schema(full_client):
    response = full_client.get("/api/catalog/videos")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 10
    assert_matches_gateway_schema(body, "/api/catalog/videos")


def test_full_catalog_search_internet_matches_gateway_schema(full_client):
    response = full_client.get("/api/catalog/search", params={"q": "internet"})
    assert response.status_code == 200
    body = response.json()
    assert_matches_gateway_schema(body, "/api/catalog/search")
    ids = {item["id"] for item in body["items"]}
    assert "UXielWVovBo" in ids
