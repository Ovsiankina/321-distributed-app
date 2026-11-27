"""Effets locaux des messages du bus (copie video_refs, idempotence)."""

from sqlalchemy.orm import Session

from .models import Favorite, ProcessedEvent, VideoRef


def apply_bus_event(db: Session, message: dict) -> None:
    event_id = str(message.get("event_id") or "")
    if not event_id or db.get(ProcessedEvent, event_id) is not None:
        return
    data = message.get("data") or {}
    kind = message.get("type")
    video_id = str(data.get("video_id") or "")
    if kind == "video.published" and video_id:
        row = db.get(VideoRef, video_id)
        if row is None:
            db.add(
                VideoRef(
                    video_id=video_id,
                    channel_id=str(data.get("channel_id") or ""),
                    title=str(data.get("title") or ""),
                )
            )
        else:
            row.channel_id = str(data.get("channel_id") or row.channel_id)
            row.title = str(data.get("title") or row.title)
    elif kind == "video.removed" and video_id:
        db.query(Favorite).filter(Favorite.video_id == video_id).delete()
        ref = db.get(VideoRef, video_id)
        if ref is not None:
            db.delete(ref)
    else:
        return
    db.add(ProcessedEvent(event_id=event_id))
    db.commit()
