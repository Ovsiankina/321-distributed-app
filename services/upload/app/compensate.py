import re
from pathlib import Path

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def delete_video_file(directory: Path, video_id: str) -> bool:
    if not VIDEO_ID_RE.match(video_id):
        return False
    removed = False
    for name in (f"{video_id}.mp4", f"{video_id}.mp4.part"):
        path = directory / name
        if path.is_file():
            path.unlink()
            removed = True
    return removed
