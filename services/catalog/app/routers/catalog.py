from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..media import resolve_thumbnail_path
from ..models import Tag, Video
from ..serialize import to_video_out

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def _prefix(request: Request) -> str:
    raw = request.headers.get("x-forwarded-prefix", "/api")
    return raw.rstrip("/") or "/api"


@router.get("/videos")
def list_videos(request: Request, db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.id).all()
    items = [to_video_out(v, _prefix(request)) for v in videos]
    return {"items": items, "total": len(items)}


@router.get("/featured")
def featured(request: Request, db: Session = Depends(get_db)):
    videos = db.query(Video).filter(Video.featured.is_(True)).order_by(Video.id).all()
    return {"items": [to_video_out(v, _prefix(request)) for v in videos]}


@router.get("/search")
def search(request: Request, q: str = Query(default=""), db: Session = Depends(get_db)):
    query_text = q.strip()
    if not query_text:
        return {"items": [], "q": q}
    like = f"%{query_text}%"
    videos = (
        db.query(Video)
        .outerjoin(Tag, Tag.video_id == Video.id)
        .filter(
            or_(
                Video.title.ilike(like),
                Video.description.ilike(like),
                Tag.tag.ilike(like),
            )
        )
        .distinct()
        .order_by(Video.id)
        .all()
    )
    return {"items": [to_video_out(v, _prefix(request)) for v in videos], "q": query_text}


@router.get("/videos/{video_id}")
def video_detail(video_id: str, request: Request, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    return to_video_out(video, _prefix(request))


@router.get("/videos/{video_id}/thumbnail")
def thumbnail(video_id: str, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    if video.thumbnail_jpeg:
        return Response(content=video.thumbnail_jpeg, media_type="image/jpeg")
    path = resolve_thumbnail_path(video.thumbnail_path, video_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    return FileResponse(path, media_type="image/jpeg")
