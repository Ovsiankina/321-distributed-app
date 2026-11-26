from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Favorite, User, VideoRef
from .auth import current_user

router = APIRouter(prefix="/api/auth/favorites", tags=["auth"])


@router.get("")
def list_favorites(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Favorite, VideoRef)
        .join(VideoRef, VideoRef.video_id == Favorite.video_id)
        .filter(Favorite.user_id == user.id)
        .all()
    )
    videos = [
        {"id": ref.video_id, "title": ref.title, "channel_id": ref.channel_id}
        for _fav, ref in rows
    ]
    return {"video_ids": [item["id"] for item in videos], "videos": videos}


@router.post("/{video_id}", status_code=201)
def add_favorite(
    video_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if db.get(VideoRef, video_id) is None:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    existing = db.get(Favorite, {"user_id": user.id, "video_id": video_id})
    if existing is None:
        db.add(Favorite(user_id=user.id, video_id=video_id))
        db.commit()
    return {"ok": True, "video_id": video_id}


@router.delete("/{video_id}", status_code=204)
def remove_favorite(
    video_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    row = db.get(Favorite, {"user_id": user.id, "video_id": video_id})
    if row is not None:
        db.delete(row)
        db.commit()
