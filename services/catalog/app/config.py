import os
from pathlib import Path

from sqlalchemy.engine import URL, make_url

SERVICE_ROOT = Path(__file__).resolve().parents[1]

CATALOG_FIXTURES_DIR = Path(
    os.environ.get("CATALOG_FIXTURES_DIR", str(SERVICE_ROOT / "fixtures"))
)

DEFAULT_DATABASE_URL = "mariadb+pymysql://catalog:catalog@localhost:3306/catalog"


def resolved_database_url() -> URL:
    raw = os.environ.get("CATALOG_DATABASE_URL", DEFAULT_DATABASE_URL)
    url = make_url(raw)
    password = os.environ.get("CATALOG_DB_PASSWORD", "")
    if password:
        url = url.set(password=password)
    return url
