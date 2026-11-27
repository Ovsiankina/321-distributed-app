import os
from pathlib import Path


class ConfigError(ValueError):
    """Variable d'environnement illisible."""


def data_dir() -> Path:
    return Path(os.environ.get("UPLOAD_DATA_DIR", "/data/videos"))


def max_upload_bytes() -> int:
    raw = os.environ.get("UPLOAD_MAX_BYTES", str(512 * 1024 * 1024))
    try:
        size = int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"UPLOAD_MAX_BYTES doit être un entier (reçu {raw!r})") from exc
    if size <= 0:
        raise ConfigError("UPLOAD_MAX_BYTES doit être strictement positif")
    return size


def amqp_url() -> str:
    return os.environ.get("UPLOAD_AMQP_URL", "").strip()
