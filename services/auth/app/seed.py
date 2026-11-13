import json
from pathlib import Path

from sqlalchemy.orm import Session

from .config import settings
from .models import User
from .passwords import hash_password
from .schemas import normalize_email


def default_users_path() -> Path:
    return settings.fixtures_dir / "users.json"


def seed_users(db: Session, path: Path | None = None) -> None:
    """Crée les comptes créateurs absents et aligne leur channel_id sur le fichier.

    Ne supprime aucun compte et ne touche pas aux mots de passe existants.
    """
    data = json.loads((path or default_users_path()).read_text(encoding="utf-8"))
    for entry in data["users"]:
        email = normalize_email(entry["email"])
        user = db.query(User).filter(User.email == email).one_or_none()
        if user is None:
            db.add(
                User(
                    email=email,
                    # Un hachage par compte : chaque sel est différent.
                    password_hash=hash_password(data["default_password"]),
                    channel_id=entry["channel_id"],
                )
            )
        else:
            user.channel_id = entry["channel_id"]
    db.commit()
