from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import CATALOG_DATA_DIR, CATALOG_DATABASE_URL
from .models import Base

CATALOG_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


engine = create_engine(CATALOG_DATABASE_URL, **_engine_kwargs(CATALOG_DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
