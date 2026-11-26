"""Publie `video.uploaded` (`origin=dataset`) pour chaque MP4 du volume.

Usage : `python -m app.announce`
"""

import asyncio
import base64

from .compensate import VIDEO_ID_RE
from .config import data_dir
from .media import make_thumbnail, probe_duration
from .messaging import publish_event


def dataset_message(video_id: str, duration: int, thumbnail: bytes) -> dict:
    return {
        "origin": "dataset",
        "video_id": video_id,
        "duration_seconds": duration,
        "thumbnail_jpeg_base64": base64.b64encode(thumbnail).decode(),
    }


async def announce() -> int:
    directory = data_dir()
    if not directory.is_dir():
        return 0
    published = 0
    for path in sorted(directory.glob("*.mp4")):
        video_id = path.name[: -len(".mp4")]
        if not VIDEO_ID_RE.match(video_id):
            continue
        duration = probe_duration(path)
        thumbnail = make_thumbnail(path) if duration else None
        if duration is None or thumbnail is None:
            continue
        await publish_event("video.uploaded", dataset_message(video_id, duration, thumbnail))
        published += 1
    return published


def main() -> int:
    print(asyncio.run(announce()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
