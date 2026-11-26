from conftest import register


def test_favorite_requires_a_known_video(client):
    token = register(client).json()["token"]
    response = client.post(
        "/api/auth/favorites/intro",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_published_event_then_favorite_roundtrip(client):
    from app.db import SessionLocal
    from app.events import apply_bus_event

    token = register(client).json()["token"]
    db = SessionLocal()
    try:
        apply_bus_event(
            db,
            {
                "event_id": "evt-1",
                "type": "video.published",
                "data": {
                    "video_id": "intro",
                    "title": "Intro",
                    "channel_id": "UC1",
                },
            },
        )
        apply_bus_event(
            db,
            {
                "event_id": "evt-1",
                "type": "video.published",
                "data": {"video_id": "intro", "title": "Autre", "channel_id": "UC1"},
            },
        )
    finally:
        db.close()

    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/auth/favorites/intro", headers=headers)
    assert created.status_code == 201
    listed = client.get("/api/auth/favorites", headers=headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["video_ids"] == ["intro"]
    assert body["videos"][0]["title"] == "Intro"

    gone = client.delete("/api/auth/favorites/intro", headers=headers)
    assert gone.status_code == 204
