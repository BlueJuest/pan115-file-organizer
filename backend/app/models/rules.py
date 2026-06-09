from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RenameRule(Base):
    __tablename__ = "rename_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), default="general")
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    sample_input: Mapped[str] = mapped_column(Text, default="")
    sample_output: Mapped[str] = mapped_column(Text, default="")
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class QualityProfile(Base):
    __tablename__ = "quality_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    resolution_weight: Mapped[float] = mapped_column(Float, default=40)
    source_weight: Mapped[float] = mapped_column(Float, default=25)
    video_codec_weight: Mapped[float] = mapped_column(Float, default=15)
    audio_codec_weight: Mapped[float] = mapped_column(Float, default=10)
    size_weight: Mapped[float] = mapped_column(Float, default=5)
    subtitle_weight: Mapped[float] = mapped_column(Float, default=5)
    min_upgrade_delta: Mapped[float] = mapped_column(Float, default=15)
    default_old_file_action: Mapped[str] = mapped_column(String(30), default="move_to_recycle")
    resolution_order: Mapped[str] = mapped_column(Text, default="2160p,1080p,720p,480p")
    source_order: Mapped[str] = mapped_column(Text, default="BluRay,WEB-DL,WEBRip,HDTV")
    video_codec_order: Mapped[str] = mapped_column(Text, default="H.265,HEVC,H.264,AVC")
    audio_codec_order: Mapped[str] = mapped_column(Text, default="TrueHD,DTS-HD,DDP,DD,AAC")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
