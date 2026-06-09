from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExecutionBatch(Base):
    __tablename__ = "execution_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scan_batches.id"), nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_batch_id: Mapped[int] = mapped_column(ForeignKey("execution_batches.id"), nullable=False)
    preview_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("preview_items.id"), nullable=True)
    file_id: Mapped[str] = mapped_column(String(100), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    before_path: Mapped[str] = mapped_column(Text, nullable=False)
    after_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    error_message: Mapped[str] = mapped_column(Text, default="")
    reversible: Mapped[int] = mapped_column(Integer, default=1)
    rolled_back: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
