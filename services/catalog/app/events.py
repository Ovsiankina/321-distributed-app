"""Traitement de video.uploaded. Le publisher (video.published / rejected) est injecté."""

import base64
import json
from collections.abc import Callable

from sqlalchemy.orm import Session

from .models import ProcessedEvent, Tag, Video

MAX_THUMBNAIL_BYTES = 256 * 1024
Publisher = Callable[[str, dict], None]


def ingest_uploaded(db: Session, message: dict, publish: Publisher) -> str:
    """Retourne published, rejected, ignored ou duplicate."""
    event_id = str(message.get("event_id") or "")
    data = message.get("data") or {}
    video_id = str(data.get("video_id") or "")
    if not event_id or not video_id:
        return "ignored"
    if db.get(ProcessedEvent, event_id) is not None:
        existing = db.get(Video, video_id)
        if existing is not None:
            publish(
                "video.published",
                {
                    "video_id": existing.id,
                    "channel_id": existing.channel_id,
                    "title": existing.title,
                },
            )
        return "duplicate"

    origin = data.get("origin")
    if origin == "dataset":
        video = db.get(Video, video_id)
        thumb = _decode_thumbnail(data.get("thumbnail_jpeg_base64"))
        if video is not None and thumb is not None:
            video.thumbnail_jpeg = thumb
        db.add(ProcessedEvent(event_id=event_id))
        db.commit()
        return "dataset"

    reason = _invalid_reason(data)
    if reason:
        publish("video.rejected", {"video_id": video_id, "reason": reason})
        db.add(ProcessedEvent(event_id=event_id))
        db.commit()
        return "rejected"

    thumb = _decode_thumbnail(data.get("thumbnail_jpeg_base64"))
    video = db.get(Video, video_id)
    qualities = json.dumps(data.get("qualities") or ["360p", "720p"])
    if video is None:
        video = Video(
            id=video_id,
            channel_id=str(data["channel_id"]),
            title=str(data["title"]),
            description=str(data.get("description") or ""),
            thumbnail_path="",
            duration_seconds=int(data["duration_seconds"]),
            featured=False,
            qualities=qualities,
            subtitle_langs="[]",
            stream_modes='["mp4"]',
            subtitle_formats="[]",
            source="upload",
            thumbnail_jpeg=thumb,
        )
        db.add(video)
        db.flush()
    else:
        video.channel_id = str(data["channel_id"])
        video.title = str(data["title"])
        video.description = str(data.get("description") or "")
        video.duration_seconds = int(data["duration_seconds"])
        video.qualities = qualities
        video.source = "upload"
        video.thumbnail_jpeg = thumb
        video.tag_rows.clear()
    for tag in data.get("tags") or []:
        db.add(Tag(tag=str(tag), video_id=video_id))
    db.add(ProcessedEvent(event_id=event_id))
    db.commit()
    publish(
        "video.published",
        {
            "video_id": video_id,
            "channel_id": str(data["channel_id"]),
            "title": str(data["title"]),
        },
    )
    return "published"


def _decode_thumbnail(raw) -> bytes | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        blob = base64.b64decode(raw, validate=True)
    except (ValueError, TypeError):
        return None
    if len(blob) > MAX_THUMBNAIL_BYTES or not blob.startswith(b"\xff\xd8"):
        return None
    return blob


def _invalid_reason(data: dict) -> str | None:
    if not str(data.get("title") or "").strip() or not str(data.get("channel_id") or "").strip():
        return "invalid_metadata"
    if not isinstance(data.get("tags"), list):
        return "invalid_metadata"
    try:
        duration = int(data.get("duration_seconds"))
    except (TypeError, ValueError):
        return "invalid_duration"
    if duration < 1:
        return "invalid_duration"
    if _decode_thumbnail(data.get("thumbnail_jpeg_base64")) is None:
        return "invalid_thumbnail"
    return None
