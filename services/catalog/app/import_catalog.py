import json
from dataclasses import dataclass
from pathlib import Path

from .config import CATALOG_FIXTURES_DIR
from .duration import duration_seconds_of

DEFAULT_QUALITIES = ("360p", "720p")


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    channel_id: str
    title: str
    description: str
    tags: tuple[str, ...]
    duration_seconds: int
    qualities: tuple[str, ...] = DEFAULT_QUALITIES
    subtitle_langs: tuple[str, ...] = ()


def _str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_tag(label: str) -> str:
    return label.strip()


def _collect_tags(item: dict) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in _str_list(item.get("tags")) + _str_list(item.get("categories")):
        tag = _normalize_tag(raw)
        key = tag.casefold()
        if not tag or key in seen:
            continue
        seen.add(key)
        out.append(tag)
    return out


def load_catalog_file(path: Path) -> list[CatalogEntry]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries: list[CatalogEntry] = []
    for item in payload.get("videos", []):
        video_id = str(item["id"])
        seconds = duration_seconds_of(item)
        if seconds < 1:
            seconds = 60
        entries.append(
            CatalogEntry(
                id=video_id,
                channel_id=str(item.get("channel_id") or "").strip(),
                title=str(item.get("title") or video_id),
                description=str(item.get("description") or ""),
                tags=tuple(_collect_tags(item)),
                duration_seconds=seconds,
                qualities=_listed(item, "qualities", DEFAULT_QUALITIES),
                subtitle_langs=_listed(item, "subtitle_langs", ()),
            )
        )
    return entries


def load_featured_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids = payload.get("video_ids") or []
    return {str(video_id) for video_id in ids}


def default_catalog_path() -> Path:
    return CATALOG_FIXTURES_DIR / "catalog.json"


def default_featured_path() -> Path:
    return CATALOG_FIXTURES_DIR / "featured.json"


def _listed(item: dict, key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if key not in item or item[key] is None:
        return default
    return tuple(_str_list(item[key]))


def stream_modes_for(_video_id: str) -> list[str]:
    return ["mp4"]


def subtitle_formats_for(langs: tuple[str, ...]) -> list[str]:
    if langs:
        return ["srt"]
    return []
