from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..media import resolve_thumbnail_path
from ..models import Tag, Video
from ..serialize import to_video_out

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("/videos")
def list_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.id).all()
    items = [to_video_out(v) for v in videos]
    return {"items": items, "total": len(items)}


@router.get("/featured")
def featured(db: Session = Depends(get_db)):
    videos = db.query(Video).filter(Video.featured.is_(True)).order_by(Video.id).all()
    return {"items": [to_video_out(v) for v in videos]}


@router.get("/search")
def search(q: str = Query(default=""), db: Session = Depends(get_db)):
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
    return {"items": [to_video_out(v) for v in videos], "q": query_text}


@router.get("/videos/{video_id}")
def video_detail(video_id: str, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    return to_video_out(video)


@router.get("/videos/{video_id}/thumbnail")
def thumbnail(video_id: str, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    path = resolve_thumbnail_path(video.thumbnail_path, video_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    return FileResponse(path, media_type="image/jpeg")
