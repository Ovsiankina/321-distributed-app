import os
from pathlib import Path

from sqlalchemy.engine import URL, make_url

SERVICE_ROOT = Path(__file__).resolve().parents[1]

CATALOG_DATA_DIR = Path(os.environ.get("CATALOG_DATA_DIR", "/data/catalog"))
CATALOG_FIXTURES_DIR = Path(
    os.environ.get("CATALOG_FIXTURES_DIR", str(SERVICE_ROOT / "fixtures"))
)
CATALOG_VIDEOS_DIR = Path(os.environ.get("CATALOG_VIDEOS_DIR", "/data/videos"))
CATALOG_SUBTITLES_DIR = Path(os.environ.get("CATALOG_SUBTITLES_DIR", "/data/subtitles"))

THUMBS_DIR = CATALOG_DATA_DIR / "thumbs"

FFMPEG_TIMEOUT_SECONDS = 30

DEFAULT_DATABASE_URL = "mariadb+pymysql://catalog:catalog@localhost:3306/catalog"


def resolved_database_url() -> URL:
    raw = os.environ.get("CATALOG_DATABASE_URL", DEFAULT_DATABASE_URL)
    url = make_url(raw)
    password = os.environ.get("CATALOG_DB_PASSWORD", "")
    if password:
        url = url.set(password=password)
    return url
