from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _exact_string(length: int) -> String:
    # MariaDB compare par défaut sans tenir compte de la casse (et, selon la
    # collation, des accents). SQLite compare octet par octet. La collation
    # binaire donne la même égalité sur les deux bases.
    return String(length).with_variant(
        VARCHAR(length, collation="utf8mb4_bin"), "mysql", "mariadb"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(_exact_string(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # Égal à videos.channel_id du service Catalog, sans clé étrangère.
    # NULL pour les comptes qui ne sont pas des créateurs.
    channel_id: Mapped[str | None] = mapped_column(_exact_string(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
