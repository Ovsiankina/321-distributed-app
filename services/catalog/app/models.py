from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text)
    thumbnail_path: Mapped[str] = mapped_column(String(512))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    qualities: Mapped[str] = mapped_column(Text)
    subtitle_langs: Mapped[str] = mapped_column(Text)
    stream_modes: Mapped[str] = mapped_column(Text)
    subtitle_formats: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(16), default="fixture")
    thumbnail_jpeg: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    tag_rows: Mapped[list["Tag"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("tag", "video_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag: Mapped[str] = mapped_column(String(128), index=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    video: Mapped[Video] = relationship(back_populates="tag_rows")
