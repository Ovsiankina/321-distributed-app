def test_mariadb_engine_enables_pool_pre_ping(client):
    from sqlalchemy import create_engine

    from app.db import _engine_kwargs

    url = "mariadb+pymysql://catalog:catalog@catalog-db:3306/catalog"
    engine = create_engine(url, **_engine_kwargs(url))
    try:
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()


def test_db_password_overrides_the_url(monkeypatch):
    from app.config import resolved_database_url

    monkeypatch.setenv(
        "CATALOG_DATABASE_URL",
        "mariadb+pymysql://catalog@catalog-db:3306/catalog",
    )
    monkeypatch.setenv("CATALOG_DB_PASSWORD", "secret/value")
    url = resolved_database_url()
    assert url.password == "secret/value"
    assert url.host == "catalog-db"
    assert url.database == "catalog"


def test_sqlite_engine_keeps_check_same_thread(client):
    from app.db import _engine_kwargs

    kwargs = _engine_kwargs("sqlite:///tmp/catalog.db")
    assert kwargs["connect_args"] == {"check_same_thread": False}
    assert "pool_pre_ping" not in kwargs