from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScanBatch(Base):
    __tablename__ = "scan_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_dir: Mapped[str] = mapped_column(String(500), nullable=False)
    target_dir: Mapped[str] = mapped_column(String(500), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), default="auto")
    recursive: Mapped[int] = mapped_column(Integer, default=1)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    recognized_count: Mapped[int] = mapped_column(Integer, default=0)
    need_confirm_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PreviewItem(Base):
    __tablename__ = "preview_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_batch_id: Mapped[int] = mapped_column(ForeignKey("scan_batches.id"), nullable=False)
    file_id: Mapped[str] = mapped_column(String(100), nullable=False)
    original_path: Mapped[str] = mapped_column(Text, nullable=False)
    new_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    media_type: Mapped[str] = mapped_column(String(20), default="unknown")
    title: Mapped[str] = mapped_column(String(255), default="")
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    season: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    episode: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tmdb_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tmdb_title: Mapped[str] = mapped_column(String(255), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0)
    matched_rule_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0)
    conflict_status: Mapped[str] = mapped_column(String(30), default="none")
    upgrade_suggestion: Mapped[str] = mapped_column(String(50), default="none")
    final_action: Mapped[str] = mapped_column(String(50), default="skip")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
