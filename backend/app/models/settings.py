from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AppSetting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    pan115_cookie: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tmdb_api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tmdb_language: Mapped[str] = mapped_column(String(20), default="zh-CN")
    default_source_dir: Mapped[str] = mapped_column(String(500), default="0")
    default_target_dir: Mapped[str] = mapped_column(String(500), default="0")
    default_recycle_dir: Mapped[str] = mapped_column(String(500), default="0")
    allow_delete_old_files: Mapped[int] = mapped_column(Integer, default=0)
    recursive_scan: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
