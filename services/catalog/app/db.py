from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import resolved_database_url
from .models import Base


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


def _database_url() -> str:
    return resolved_database_url().render_as_string(hide_password=False)


engine = create_engine(_database_url(), **_engine_kwargs(_database_url()))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def ping_database() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
