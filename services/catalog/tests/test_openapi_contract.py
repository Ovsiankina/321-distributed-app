from gateway_openapi import assert_matches_gateway_schema


def test_video_object_matches_gateway_video_schema(client):
    response = client.get("/api/catalog/videos/test-video-one")
    assert response.status_code == 200
    assert_matches_gateway_schema(
        response.json(),
        "/api/catalog/videos/{video_id}",
    )


def test_list_items_match_gateway_video_schema(client):
    response = client.get("/api/catalog/videos")
    assert response.status_code == 200
    body = response.json()
    assert_matches_gateway_schema(body, "/api/catalog/videos")
    for item in body["items"]:
        assert item["thumbnail_url"] == f"/api/catalog/videos/{item['id']}/thumbnail"
