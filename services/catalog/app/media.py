import subprocess
from pathlib import Path

from .config import CATALOG_DATA_DIR, CATALOG_VIDEOS_DIR, THUMBS_DIR


def thumbnail_relative_path(video_id: str) -> str:
    return f"thumbs/{video_id}.jpg"


def thumb_path(video_id: str) -> Path:
    return THUMBS_DIR / f"{video_id}.jpg"


def resolve_thumbnail_path(thumbnail_path: str | None, video_id: str) -> Path:
    rel = (thumbnail_path or "").strip() or thumbnail_relative_path(video_id)
    return CATALOG_DATA_DIR / rel


def ensure_thumbnail(video_id: str) -> Path | None:
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    dest = thumb_path(video_id)
    if dest.is_file():
        return dest
    source = CATALOG_VIDEOS_DIR / f"{video_id}.mp4"
    if not source.is_file():
        return None
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        "30",
        "-i",
        str(source),
        "-frames:v",
        "1",
        "-q:v",
        "3",
        str(dest),
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return dest if dest.is_file() else None
