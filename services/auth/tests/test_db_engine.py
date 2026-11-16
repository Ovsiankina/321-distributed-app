def test_mariadb_engine_enables_pool_pre_ping(auth_env):
    from sqlalchemy import create_engine

    from app.db import _engine_kwargs

    url = "mariadb+pymysql://auth:auth@auth-db:3306/auth"
    engine = create_engine(url, **_engine_kwargs(url))
    try:
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()


def test_email_and_channel_id_use_a_binary_collation_on_mariadb(auth_env):
    from sqlalchemy.dialects.mysql.mariadb import MariaDBDialect
    from sqlalchemy.schema import CreateTable

    from app.models import User

    ddl = str(CreateTable(User.__table__).compile(dialect=MariaDBDialect()))
    assert "email VARCHAR(255) COLLATE utf8mb4_bin NOT NULL" in ddl
    assert "channel_id VARCHAR(64) COLLATE utf8mb4_bin" in ddl
