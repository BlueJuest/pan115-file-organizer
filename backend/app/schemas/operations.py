from datetime import datetime

from pydantic import BaseModel, Field


class ExecutionCreate(BaseModel):
    preview_item_ids: list[int] = Field(default_factory=list)
    fail_fast: bool = False


class ExecutionRead(BaseModel):
    id: int
    scan_batch_id: int | None
    item_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    status: str
    created_at: datetime
    completed_at: datetime | None


class OperationLogRead(BaseModel):
    id: int
    execution_batch_id: int
    preview_item_id: int | None
    file_id: str
    operation_type: str
    before_path: str
    after_path: str
    status: str
    error_message: str
    reversible: bool
    rolled_back: bool
    created_at: datetime


class RollbackPlanItem(BaseModel):
    operation_log_id: int
    file_id: str
    current_path: str
    rollback_path: str
    reversible: bool


class RollbackPlan(BaseModel):
    execution_batch_id: int
    items: list[RollbackPlanItem] = Field(default_factory=list)
