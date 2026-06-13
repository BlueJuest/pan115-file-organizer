from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.mock_pan115 import MockPan115Client
from app.core.database import get_db
from app.models import ExecutionBatch, OperationLog
from app.schemas.operations import ExecutionRead, RollbackPlan, RollbackPlanItem
from app.services.rollback import RollbackService

router = APIRouter(prefix="/api", tags=["rollback"])


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


@router.post("/executions/{execution_id}/rollback-plan", response_model=RollbackPlan)
def create_rollback_plan(execution_id: int, db: Session = Depends(get_db)) -> RollbackPlan:
    batch = db.get(ExecutionBatch, execution_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="执行批次不存在")
    logs = db.scalars(
        select(OperationLog)
        .where(
            OperationLog.execution_batch_id == execution_id,
            OperationLog.status == "success",
            OperationLog.reversible == 1,
            OperationLog.rolled_back == 0,
        )
        .order_by(OperationLog.id.desc())
    ).all()
    return RollbackPlan(
        execution_batch_id=execution_id,
        items=[
            RollbackPlanItem(
                operation_log_id=log.id,
                file_id=log.file_id,
                current_path=log.after_path,
                rollback_path=log.before_path,
                reversible=bool(log.reversible),
            )
            for log in logs
        ],
    )


@router.post("/rollbacks/{execution_id}", response_model=ExecutionRead)
def rollback_execution(execution_id: int, db: Session = Depends(get_db)) -> ExecutionRead:
    batch = db.get(ExecutionBatch, execution_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="执行批次不存在")
    rollback_batch = RollbackService(MockPan115Client()).rollback_execution(db, execution_id)
    return execution_to_read(rollback_batch)
