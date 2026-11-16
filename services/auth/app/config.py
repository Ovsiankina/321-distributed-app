import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

SERVICE_ROOT = Path(__file__).resolve().parents[1]


class ConfigError(ValueError):
    """Variable d'environnement absente ou illisible."""


@dataclass(frozen=True)
class Settings:
    database_url: URL
    jwt_private_key: Ed25519PrivateKey
    jwt_issuer: str
    jwt_audience: str
    token_ttl_hours: int
    fixtures_dir: Path


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} est obligatoire")
    return value


def _database_url() -> URL:
    raw = _required("AUTH_DATABASE_URL")
    try:
        url = make_url(raw)
    except ArgumentError as exc:
        raise ConfigError(
            "AUTH_DATABASE_URL n'est pas une URL SQLAlchemy lisible"
        ) from exc
    password = os.environ.get("AUTH_DB_PASSWORD")
    if password:
        # Passé à part, le mot de passe n'est jamais relu comme une URL :
        # @, :, /, # ou % n'y déplacent pas l'hôte ni la base.
        url = url.set(password=password)
    return url


def _private_key() -> Ed25519PrivateKey:
    pem = _required("AUTH_JWT_PRIVATE_KEY")
    try:
        key = load_pem_private_key(pem.encode(), password=None)
    except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
        raise ConfigError("AUTH_JWT_PRIVATE_KEY n'est pas une clé PEM lisible") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise ConfigError("AUTH_JWT_PRIVATE_KEY doit être une clé Ed25519")
    return key


def _token_ttl_hours() -> int:
    raw = os.environ.get("AUTH_TOKEN_TTL_HOURS", "1")
    try:
        hours = int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"AUTH_TOKEN_TTL_HOURS doit être un entier (reçu {raw!r})"
        ) from exc
    if hours < 1:
        raise ConfigError(f"AUTH_TOKEN_TTL_HOURS doit valoir au moins 1 (reçu {raw!r})")
    return hours


def load_settings() -> Settings:
    return Settings(
        database_url=_database_url(),
        jwt_private_key=_private_key(),
        jwt_issuer=os.environ.get("AUTH_JWT_ISSUER") or "stream321-auth",
        jwt_audience=os.environ.get("AUTH_JWT_AUDIENCE") or "stream321-api",
        token_ttl_hours=_token_ttl_hours(),
        fixtures_dir=Path(
            os.environ.get("AUTH_FIXTURES_DIR") or SERVICE_ROOT / "fixtures"
        ),
    )


# Lu à l'import : une configuration incomplète arrête le service avant qu'il écoute.
settings = load_settings()
