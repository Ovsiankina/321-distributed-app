from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Quality = Literal["360p", "720p"]
StreamMode = Literal["mp4", "hls"]
SubtitleFormat = Literal["srt", "vtt"]


class VideoOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    tags: list[str]
    duration_seconds: int = Field(ge=1)
    thumbnail_url: str
    qualities: list[Quality]
    featured: bool
    subtitle_langs: list[str]
    stream_modes: list[StreamMode]
    subtitle_formats: list[SubtitleFormat]


class VideoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[VideoOut]
    total: int = Field(ge=0)


class VideoItemsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[VideoOut]


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[VideoOut]
    q: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: str
