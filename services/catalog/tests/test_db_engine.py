def test_mariadb_engine_enables_pool_pre_ping(client):
    from sqlalchemy import create_engine

    from app.db import _engine_kwargs

    url = "mariadb+pymysql://catalog:catalog@catalog-db:3306/catalog"
    engine = create_engine(url, **_engine_kwargs(url))
    try:
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()


def test_sqlite_engine_keeps_check_same_thread(client):
    from app.db import _engine_kwargs

    kwargs = _engine_kwargs("sqlite:///tmp/catalog.db")
    assert kwargs["connect_args"] == {"check_same_thread": False}
    assert "pool_pre_ping" not in kwargs