import json

from .models import Video
from .schemas import VideoOut


def _json_list(raw: str) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def to_video_out(video: Video) -> VideoOut:
    tags = sorted({row.tag for row in video.tag_rows})
    return VideoOut(
        id=video.id,
        title=video.title,
        description=video.description,
        tags=tags,
        duration_seconds=video.duration_seconds,
        thumbnail_url=f"/api/catalog/videos/{video.id}/thumbnail",
        qualities=_json_list(video.qualities),
        featured=video.featured,
        subtitle_langs=_json_list(video.subtitle_langs),
        stream_modes=_json_list(video.stream_modes),
        subtitle_formats=_json_list(video.subtitle_formats),
    )
