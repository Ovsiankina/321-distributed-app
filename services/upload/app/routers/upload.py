import base64
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from .. import messaging
from ..compensate import delete_video_file
from ..config import data_dir, max_upload_bytes
from ..identity import require_creator
from ..media import make_thumbnail, probe_duration

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/videos", status_code=202)
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
):
    _user_id, channel_id = require_creator(request)
    if (file.content_type or "").lower() != "video/mp4":
        raise HTTPException(status_code=415, detail="Type de média non supporté")
    if not title.strip():
        raise HTTPException(status_code=400, detail="Titre requis")

    video_id = uuid.uuid4().hex
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    partial = directory / f"{video_id}.mp4.part"
    final = directory / f"{video_id}.mp4"
    written = 0
    limit = max_upload_bytes()
    try:
        with partial.open("wb") as handle:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > limit:
                    raise HTTPException(status_code=413, detail="Fichier trop volumineux")
                handle.write(chunk)
        if written == 0:
            raise HTTPException(status_code=400, detail="Fichier requis")
        os.replace(partial, final)
    except HTTPException:
        partial.unlink(missing_ok=True)
        final.unlink(missing_ok=True)
        raise

    duration = probe_duration(final)
    thumbnail = make_thumbnail(final) if duration else None
    if duration is None or thumbnail is None:
        final.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Vidéo illisible")

    tag_list = [part.strip() for part in tags.split(",") if part.strip()]
    payload = {
        "origin": "upload",
        "video_id": video_id,
        "channel_id": channel_id,
        "title": title.strip(),
        "description": description,
        "tags": tag_list,
        "duration_seconds": duration,
        "qualities": ["360p", "720p"],
        "thumbnail_jpeg_base64": base64.b64encode(thumbnail).decode(),
        "uploaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        await messaging.publish_event("video.uploaded", payload)
    except Exception:
        final.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail="Service indisponible") from None
    return {"video_id": video_id, "status": "processing"}


def apply_rejection(video_id: str) -> None:
    delete_video_file(data_dir(), video_id)
