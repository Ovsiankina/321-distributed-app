import json
from pathlib import Path

from sqlalchemy.orm import Session

from .config import settings
from .models import User
from .passwords import hash_password
from .schemas import normalize_email


def default_users_path() -> Path:
    return settings.fixtures_dir / "users.json"


def _channels_by_email(entries: list[dict]) -> dict[str, str]:
    """Chaîne de chaque email normalisé. Refuse un fichier contradictoire."""
    channels: dict[str, str] = {}
    owners: dict[str, str] = {}
    for entry in entries:
        email = normalize_email(entry["email"])
        channel_id = entry["channel_id"]
        # Deux écritures d'un même email (casse, espaces) ne font qu'un compte.
        if channels.setdefault(email, channel_id) != channel_id:
            raise ValueError(f"users.json : {email} a plusieurs channel_id")
        if owners.setdefault(channel_id, email) != email:
            raise ValueError(
                f"users.json : {channel_id} appartient à plusieurs comptes"
            )
    return channels


def seed_users(db: Session, path: Path | None = None) -> None:
    """Crée les comptes créateurs absents et leur donne le channel_id du fichier.

    Le fichier fait foi pour les chaînes qu'il liste : une chaîne tenue par un autre
    compte lui est retirée. Ne supprime aucun compte et ne touche pas aux mots de
    passe existants.
    """
    data = json.loads((path or default_users_path()).read_text(encoding="utf-8"))
    wanted = _channels_by_email(data["users"])

    # Libérer d'abord les chaînes qui changent de compte. Sans ce flush séparé, une
    # chaîne passée à un autre email, ou deux comptes qui échangent leur chaîne,
    # violeraient UNIQUE(channel_id).
    holders = db.query(User).filter(User.channel_id.in_(list(wanted.values())))
    for user in holders:
        if wanted.get(user.email) != user.channel_id:
            user.channel_id = None
    db.flush()

    existing = {
        user.email: user for user in db.query(User).filter(User.email.in_(list(wanted)))
    }
    for email, channel_id in wanted.items():
        user = existing.get(email)
        if user is None:
            db.add(
                User(
                    email=email,
                    # Un hachage par compte : chaque sel est différent.
                    password_hash=hash_password(data["default_password"]),
                    channel_id=channel_id,
                )
            )
        else:
            user.channel_id = channel_id
    db.commit()
