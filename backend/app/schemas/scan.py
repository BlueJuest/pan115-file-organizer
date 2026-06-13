from datetime import datetime

from pydantic import BaseModel


class ScanCreate(BaseModel):
    source_dir: str
    target_dir: str
    media_type: str = "auto"
    recursive: bool = True


class ScanRead(BaseModel):
    id: int
    source_dir: str
    target_dir: str
    media_type: str
    recursive: bool
    file_count: int
    recognized_count: int
    need_confirm_count: int
    status: str
    created_at: datetime


class PreviewItemRead(BaseModel):
    id: int
    scan_batch_id: int
    file_id: str
    original_path: str
    new_path: str
    file_size: int
    media_type: str
    title: str
    year: int | None
    season: int | None
    episode: int | None
    tmdb_id: int | None
    tmdb_title: str
    confidence: float
    matched_rule_id: int | None
    quality_score: float
    conflict_status: str
    upgrade_suggestion: str
    final_action: str
    status: str
    error_message: str
    created_at: datetime


class PreviewItemUpdate(BaseModel):
    new_path: str | None = None
    media_type: str | None = None
    final_action: str | None = None
    status: str | None = None
