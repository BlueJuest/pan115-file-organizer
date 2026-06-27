from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ExecutionBatch, OperationLog
from app.schemas.operations import ExecutionCreate, ExecutionRead, OperationLogRead
from app.services.client_factory import ClientConfigError, ClientFactory
from app.services.executor import Executor

router = APIRouter(prefix="/api/executions", tags=["executions"])
CLIENT_FACTORY_CLASS = ClientFactory


def execution_to_read(batch: ExecutionBatch) -> ExecutionRead:
    return ExecutionRead(
        id=batch.id,
        scan_batch_id=batch.scan_batch_id,
        item_count=batch.item_count,
        success_count=batch.success_count,
        failed_count=batch.failed_count,
        skipped_count=batch.skipped_count,
        status=batch.status,
        created_at=batch.created_at,
        completed_at=batch.completed_at,
    )


def operation_log_to_read(log: OperationLog) -> OperationLogRead:
    return OperationLogRead(
        id=log.id,
        execution_batch_id=log.execution_batch_id,
        preview_item_id=log.preview_item_id,
        file_id=log.file_id,
        operation_type=log.operation_type,
        before_path=log.before_path,
        after_path=log.after_path,
        status=log.status,
        error_message=log.error_message,
        reversible=bool(log.reversible),
        rolled_back=bool(log.rolled_back),
        created_at=log.created_at,
    )


@router.post("", response_model=ExecutionRead)
def create_execution(payload: ExecutionCreate, db: Session = Depends(get_db)) -> ExecutionRead:
    try:
        pan_client = CLIENT_FACTORY_CLASS(db).pan115()
    except ClientConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    batch = Executor(pan_client).execute(db, payload.preview_item_ids, payload.fail_fast)
    return execution_to_read(batch)


@router.get("/{execution_id}", response_model=ExecutionRead)
def get_execution(execution_id: int, db: Session = Depends(get_db)) -> ExecutionRead:
    batch = db.get(ExecutionBatch, execution_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="执行批次不存在")
    return execution_to_read(batch)


@router.get("/{execution_id}/logs", response_model=list[OperationLogRead])
def list_execution_logs(execution_id: int, db: Session = Depends(get_db)) -> list[OperationLogRead]:
    batch = db.get(ExecutionBatch, execution_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="执行批次不存在")
    logs = db.scalars(
        select(OperationLog).where(OperationLog.execution_batch_id == execution_id).order_by(OperationLog.id)
    ).all()
    return [operation_log_to_read(log) for log in logs]
