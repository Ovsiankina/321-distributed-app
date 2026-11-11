def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "catalog"}


def test_health_returns_503_when_database_is_down(client, monkeypatch):
    from sqlalchemy.exc import OperationalError

    import app.db as db

    def broken_connect(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("db down"))

    monkeypatch.setattr(db.engine, "connect", broken_connect)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "service": "catalog"}
