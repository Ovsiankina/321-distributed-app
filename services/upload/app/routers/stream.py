from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from ..compensate import VIDEO_ID_RE
from ..config import data_dir

router = APIRouter(prefix="/api/stream", tags=["streaming"])


def _parse_range(header: str, size: int) -> tuple[int, int] | None:
    if not header.startswith("bytes="):
        return None
    spec = header.removeprefix("bytes=").split(",", 1)[0].strip()
    if "-" not in spec:
        return None
    start_raw, end_raw = spec.split("-", 1)
    if start_raw == "":
        return None
    try:
        start = int(start_raw)
        end = int(end_raw) if end_raw else size - 1
    except ValueError:
        return None
    if start < 0 or start >= size or end < start:
        return None
    return start, min(end, size - 1)


def _stream(video_id: str, quality: str | None, request: Request, include_body: bool) -> Response:
    if not VIDEO_ID_RE.match(video_id):
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    if quality not in (None, "360p", "720p"):
        raise HTTPException(status_code=400, detail="Qualité inconnue (360p ou 720p)")
    path = data_dir() / f"{video_id}.mp4"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    size = path.stat().st_size
    selected = _parse_range(request.headers.get("range", ""), size)
    headers = {"Accept-Ranges": "bytes", "Content-Type": "video/mp4"}
    if selected is None:
        body = path.read_bytes() if include_body else b""
        headers["Content-Length"] = str(size)
        return Response(content=body, status_code=200, headers=headers, media_type="video/mp4")
    start, end = selected
    length = end - start + 1
    headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    headers["Content-Length"] = str(length)
    body = b""
    if include_body:
        with path.open("rb") as handle:
            handle.seek(start)
            body = handle.read(length)
    return Response(content=body, status_code=206, headers=headers, media_type="video/mp4")


@router.get("/{video_id}")
def stream_get(
    video_id: str,
    request: Request,
    quality: str | None = Query(default=None),
):
    return _stream(video_id, quality, request, True)


@router.head("/{video_id}")
def stream_head(
    video_id: str,
    request: Request,
    quality: str | None = Query(default=None),
):
    return _stream(video_id, quality, request, False)
