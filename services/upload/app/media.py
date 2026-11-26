import subprocess
from pathlib import Path

FFMPEG_TIMEOUT_SECONDS = 30


def probe_duration(path: Path) -> int | None:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
        seconds = int(float(completed.stdout.strip()))
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
        return None
    return seconds if seconds >= 1 else None


def make_thumbnail(path: Path) -> bytes | None:
    for offset in ("30", "1"):
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            offset,
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-vf",
            "scale=480:-2",
            "-q:v",
            "3",
            "-f",
            "image2pipe",
            "-c:v",
            "mjpeg",
            "-",
        ]
        try:
            completed = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=FFMPEG_TIMEOUT_SECONDS,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
        if completed.stdout.startswith(b"\xff\xd8"):
            return completed.stdout
    return None
