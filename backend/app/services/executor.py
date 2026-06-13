from datetime import datetime
from pathlib import PurePosixPath

from sqlalchemy.orm import Session

from app.clients.protocols import Pan115ClientProtocol
from app.models import ExecutionBatch, OperationLog, PreviewItem


class Executor:
    def __init__(self, pan_client: Pan115ClientProtocol) -> None:
        self.pan_client = pan_client

    def execute(self, db: Session, preview_item_ids: list[int], fail_fast: bool) -> ExecutionBatch:
        batch = ExecutionBatch(item_count=len(preview_item_ids), status="running")
        db.add(batch)
        db.flush()

        for item_id in preview_item_ids:
            item = db.get(PreviewItem, item_id)
            if item is None or item.final_action == "skip":
                batch.skipped_count += 1
                continue

            log = OperationLog(
                execution_batch_id=batch.id,
                preview_item_id=item.id,
                file_id=item.file_id,
                operation_type=item.final_action,
                before_path=item.original_path,
                after_path=item.new_path,
                reversible=0 if item.final_action == "delete_old" else 1,
            )
            db.add(log)

            try:
                result = self._execute_item(item)
                if result.ok:
                    log.status = "success"
                    item.status = "executed"
                    batch.success_count += 1
                else:
                    log.status = "failed"
                    log.error_message = result.message
                    item.status = "failed"
                    item.error_message = result.message
                    batch.failed_count += 1
                    if fail_fast:
                        break
            except Exception as exc:
                message = str(exc)
                log.status = "failed"
                log.error_message = message
                item.status = "failed"
                item.error_message = message
                batch.failed_count += 1
                if fail_fast:
                    break

        batch.status = "completed" if batch.failed_count == 0 else "partial_failed"
        batch.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(batch)
        return batch

    def _execute_item(self, item: PreviewItem):
        new_path = PurePosixPath(item.new_path)
        if item.final_action in {"rename", "rename_move"}:
            return self.pan_client.rename(item.file_id, new_path.name)
        if item.final_action == "move":
            return self.pan_client.move(item.file_id, new_path.parent.as_posix())
        if item.final_action == "delete_old":
            return self.pan_client.delete(item.file_id)
        raise ValueError(f"unsupported action: {item.final_action}")
