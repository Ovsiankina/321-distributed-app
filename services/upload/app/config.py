import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

JWT_LEEWAY_SECONDS = 30
JWT_ALGORITHM = "EdDSA"


class ConfigError(ValueError):
    """Variable d'environnement illisible."""


@dataclass(frozen=True)
class JwtSettings:
    public_key: Ed25519PublicKey
    issuer: str
    audience: str


def data_dir() -> Path:
    return Path(os.environ.get("UPLOAD_DATA_DIR", "/data/upload/incoming"))


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


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} est obligatoire")
    return value


def load_jwt_settings() -> JwtSettings:
    pem = _required("UPLOAD_JWT_PUBLIC_KEY")
    try:
        key = load_pem_public_key(pem.encode())
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        raise ConfigError("UPLOAD_JWT_PUBLIC_KEY n'est pas une clé publique PEM Ed25519") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise ConfigError("UPLOAD_JWT_PUBLIC_KEY doit être une clé Ed25519")
    issuer = os.environ.get("UPLOAD_JWT_ISSUER", "stream321-auth").strip()
    audience = os.environ.get("UPLOAD_JWT_AUDIENCE", "stream321-api").strip()
    if not issuer or not audience:
        raise ConfigError("UPLOAD_JWT_ISSUER et UPLOAD_JWT_AUDIENCE sont obligatoires")
    return JwtSettings(public_key=key, issuer=issuer, audience=audience)