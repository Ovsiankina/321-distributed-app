import json
from pathlib import Path

from sqlalchemy.orm import Session

from .import_catalog import (
    CatalogEntry,
    default_catalog_path,
    default_featured_path,
    load_catalog_file,
    load_featured_ids,
    qualities_for,
    stream_modes_for,
    subtitle_formats_for,
    subtitle_langs_for,
)
from .media import ensure_thumbnail, thumbnail_relative_path
from .models import Tag, Video


def _replace_tags(db: Session, pairs: list[tuple[str, str]]) -> None:
    db.query(Tag).delete()
    seen: set[tuple[str, str]] = set()
    for label, video_id in pairs:
        key = (label, video_id)
        if not label or key in seen:
            continue
        seen.add(key)
        db.add(Tag(tag=label, video_id=video_id))


def _video_fields(entry: CatalogEntry, featured_ids: set[str]) -> dict:
    langs = subtitle_langs_for(entry.id)
    return {
        "channel_id": entry.channel_id,
        "title": entry.title,
        "description": entry.description,
        "thumbnail_path": thumbnail_relative_path(entry.id),
        "duration_seconds": entry.duration_seconds,
        "featured": entry.id in featured_ids,
        "qualities": json.dumps(qualities_for(entry.id)),
        "subtitle_langs": json.dumps(langs),
        "stream_modes": json.dumps(stream_modes_for(entry.id)),
        "subtitle_formats": json.dumps(subtitle_formats_for(entry.id)),
    }


def sync_catalog_db(
    db: Session,
    catalog_path: Path | None = None,
    featured_path: Path | None = None,
) -> None:
    catalog_path = catalog_path or default_catalog_path()
    featured_path = featured_path or default_featured_path()
    entries = load_catalog_file(catalog_path)
    featured_ids = load_featured_ids(featured_path)
    valid = {entry.id for entry in entries}

    for row in list(db.query(Video).all()):
        if row.id not in valid:
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
    )
    db.commit()

    for entry in entries:
        ensure_thumbnail(entry.id)


def seed_if_empty(db: Session) -> None:
    sync_catalog_db(db)
