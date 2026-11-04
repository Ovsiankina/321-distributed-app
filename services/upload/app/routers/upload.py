from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..auth import require_authenticated_user
from ..catalog_client import ensure_catalog_ready

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/videos")
def upload_video(
    _user: dict = Depends(require_authenticated_user),
    file: UploadFile = File(...),
):
    ensure_catalog_ready()
    if not file.filename:
        raise HTTPException(status_code=400, detail="Fichier requis")
    content_type = (file.content_type or "").lower()
    if content_type and not content_type.startswith("video/"):
        raise HTTPException(status_code=415, detail="Type de média non supporté")
    raise HTTPException(
        status_code=501,
        detail="Upload vidéo non implémenté (squelette)",
    )
