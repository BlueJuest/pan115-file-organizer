from datetime import datetime
from pathlib import PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.protocols import Pan115ClientProtocol
from app.models import ExecutionBatch, OperationLog


class RollbackService:
    def __init__(self, pan_client: Pan115ClientProtocol) -> None:
        self.pan_client = pan_client

    def rollback_execution(self, db: Session, execution_batch_id: int) -> ExecutionBatch:
        logs = db.scalars(
            select(OperationLog)
            .where(
                OperationLog.execution_batch_id == execution_batch_id,
                OperationLog.status == "success",
                OperationLog.reversible == 1,
                OperationLog.rolled_back == 0,
            )
            .order_by(OperationLog.id.desc())
        ).all()

        rollback_batch = ExecutionBatch(item_count=len(logs), status="running")
        db.add(rollback_batch)
        db.flush()

        for original_log in logs:
            rollback_log = OperationLog(
                execution_batch_id=rollback_batch.id,
                preview_item_id=original_log.preview_item_id,
                file_id=original_log.file_id,
                operation_type="rollback",
                before_path=original_log.after_path,
                after_path=original_log.before_path,
                reversible=0,
            )
            db.add(rollback_log)

            try:
                result = self._rollback_log(original_log)
                if result.ok:
                    rollback_log.status = "success"
                    original_log.rolled_back = 1
                    rollback_batch.success_count += 1
                else:
                    rollback_log.status = "failed"
                    rollback_log.error_message = result.message
                    rollback_batch.failed_count += 1
            except Exception as exc:
                rollback_log.status = "failed"
                rollback_log.error_message = str(exc)
                rollback_batch.failed_count += 1

        rollback_batch.status = "completed" if rollback_batch.failed_count == 0 else "partial_failed"
        rollback_batch.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(rollback_batch)
        return rollback_batch

    def _rollback_log(self, log: OperationLog):
        before_path = PurePosixPath(log.before_path)
        if log.operation_type in {"rename", "rename_move"}:
            return self.pan_client.rename(log.file_id, before_path.name)
        if log.operation_type == "move":
            return self.pan_client.move(log.file_id, before_path.parent.as_posix())
        raise ValueError(f"unsupported rollback operation: {log.operation_type}")
