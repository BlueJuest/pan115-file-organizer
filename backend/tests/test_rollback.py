from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.clients.mock_pan115 import MockPan115Client
from app.clients.protocols import RemoteFile
from app.models import ExecutionBatch, OperationLog
from app.models.base import Base
from app.services.rollback import RollbackService


def test_rollback_execution_reverses_successful_rename_and_writes_rollback_log():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    pan = MockPan115Client(
        [RemoteFile("f1", "新名.mkv", "/下载/新名.mkv", "src", False, 1)]
    )

    with Session(engine) as db:
        batch = ExecutionBatch(item_count=1, success_count=1, status="completed")
        db.add(batch)
        db.flush()
        db.add(
            OperationLog(
                execution_batch_id=batch.id,
                file_id="f1",
                operation_type="rename",
                before_path="/下载/旧名.mkv",
                after_path="/下载/新名.mkv",
                status="success",
                reversible=1,
            )
        )
        db.commit()

        rollback_batch = RollbackService(pan).rollback_execution(db, batch.id)

        db.refresh(rollback_batch)
        rollback_log = db.scalars(
            select(OperationLog).where(OperationLog.operation_type == "rollback")
        ).one()
        assert rollback_batch.success_count == 1
        assert rollback_log.status == "success"
        assert pan.get_path("f1") == "/下载/旧名.mkv"
