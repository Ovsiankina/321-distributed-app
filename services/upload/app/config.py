import os
from pathlib import Path


class ConfigError(ValueError):
    """Variable d'environnement illisible."""


def data_dir() -> Path:
    return Path(os.environ.get("UPLOAD_DATA_DIR", "/data/upload/incoming"))


def jwt_secret() -> str:
    return os.environ.get("UPLOAD_JWT_SECRET", "dev-upload-jwt-secret")


def jwt_algorithm() -> str:
    return os.environ.get("UPLOAD_JWT_ALGORITHM", "HS256")


def catalog_base_url() -> str:
    return os.environ.get("UPLOAD_CATALOG_URL", "http://127.0.0.1:8002")


def catalog_timeout_seconds() -> float:
    name = "UPLOAD_CATALOG_TIMEOUT_SECONDS"
    raw = os.environ.get(name, "3.0")
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(
            f"{name} doit être un nombre (valeur reçue : {raw!r})"
        ) from exc
    if timeout <= 0:
        raise ConfigError(
            f"{name} doit être strictement positif (valeur reçue : {raw!r})"
        )
    return timeout
