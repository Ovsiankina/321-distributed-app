import os
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]

CATALOG_DATA_DIR = Path(os.environ.get("CATALOG_DATA_DIR", "/data/catalog"))
CATALOG_FIXTURES_DIR = Path(
    os.environ.get("CATALOG_FIXTURES_DIR", str(SERVICE_ROOT / "fixtures"))
)
CATALOG_VIDEOS_DIR = Path(os.environ.get("CATALOG_VIDEOS_DIR", "/data/videos"))
CATALOG_SUBTITLES_DIR = Path(os.environ.get("CATALOG_SUBTITLES_DIR", "/data/subtitles"))

THUMBS_DIR = CATALOG_DATA_DIR / "thumbs"

DEFAULT_DATABASE_URL = "mariadb+pymysql://catalog:catalog@localhost:3306/catalog"
CATALOG_DATABASE_URL = os.environ.get("CATALOG_DATABASE_URL", DEFAULT_DATABASE_URL)
