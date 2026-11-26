import json
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from .import_catalog import (
    CatalogEntry,
    default_catalog_path,
    default_featured_path,
    load_catalog_file,
    load_featured_ids,
    stream_modes_for,
    subtitle_formats_for,
)
from .models import Tag, Video


class CatalogSync:
    def __init__(self, removed: list[dict]):
        self.removed = removed


def _replace_tags(db: Session, pairs: list[tuple[str, str]], video_ids: set[str]) -> None:
    if video_ids:
        db.query(Tag).filter(Tag.video_id.in_(video_ids)).delete(synchronize_session=False)
    seen: set[tuple[str, str]] = set()
    for label, video_id in pairs:
        key = (label, video_id)
        if not label or key in seen:
            continue
        seen.add(key)
        db.add(Tag(tag=label, video_id=video_id))


def _video_fields(entry: CatalogEntry, featured_ids: set[str]) -> dict:
    return {
        "channel_id": entry.channel_id,
        "title": entry.title,
        "description": entry.description,
        "thumbnail_path": "",
        "duration_seconds": entry.duration_seconds,
        "featured": entry.id in featured_ids,
        "qualities": json.dumps(list(entry.qualities)),
        "subtitle_langs": json.dumps(list(entry.subtitle_langs)),
        "stream_modes": json.dumps(stream_modes_for(entry.id)),
        "subtitle_formats": json.dumps(subtitle_formats_for(entry.subtitle_langs)),
    }


def sync_catalog_db(
    db: Session,
    catalog_path: Path | None = None,
    featured_path: Path | None = None,
) -> CatalogSync:
    catalog_path = catalog_path or default_catalog_path()
    featured_path = featured_path or default_featured_path()
    entries = load_catalog_file(catalog_path)
    featured_ids = load_featured_ids(featured_path)
    valid = {entry.id for entry in entries}
    removed: list[dict] = []

    for row in list(db.query(Video).all()):
        if row.id in valid or row.source == "upload":
            continue
        removed.append(
            {"video_id": row.id, "channel_id": row.channel_id, "title": row.title}
        )
        db.delete(row)

    for entry in entries:
        fields = _video_fields(entry, featured_ids)
        row = db.get(Video, entry.id)
        if row is None:
            db.add(Video(id=entry.id, **fields))
        else:
            for key, value in fields.items():
                setattr(row, key, value)

    db.flush()
    _replace_tags(
        db,
        [(tag, entry.id) for entry in entries for tag in entry.tags],
        valid,
    )
    db.commit()
    return CatalogSync(removed)


@contextmanager
def catalog_sync_lock(db: Session, blocking: bool = True):
    bind = db.get_bind()
    if bind.dialect.name == "sqlite":
        yield
        return
    timeout = 30 if blocking else 0
    connection = db.connection()
    acquired = connection.execute(
        text("SELECT GET_LOCK('catalog_sync', :timeout)"),
        {"timeout": timeout},
    ).scalar()
    if acquired != 1:
        raise BlockingIOError("catalog_sync")
    try:
        yield
    finally:
        connection.execute(text("SELECT RELEASE_LOCK('catalog_sync')"))


def sync_catalog_on_startup(db: Session) -> CatalogSync:
    with catalog_sync_lock(db):
        return sync_catalog_db(db)
