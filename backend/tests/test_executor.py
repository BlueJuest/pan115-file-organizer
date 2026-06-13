from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.clients.mock_pan115 import MockPan115Client
from app.clients.protocols import RemoteFile
from app.models import ExecutionBatch, OperationLog, PreviewItem, ScanBatch
from app.models.base import Base
from app.services.executor import Executor


def test_executor_renames_item_and_writes_success_log():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    pan = MockPan115Client(
        [RemoteFile("f1", "旧名.mkv", "/下载/旧名.mkv", "src", False, 1)]
    )

    with Session(engine) as db:
        scan_batch = ScanBatch(source_dir="/下载", target_dir="/下载")
        db.add(scan_batch)
        db.flush()
        item = PreviewItem(
            scan_batch_id=scan_batch.id,
            file_id="f1",
            original_path="/下载/旧名.mkv",
            new_path="/下载/新名.mkv",
            final_action="rename",
        )
        db.add(item)
        db.commit()

        batch = Executor(pan).execute(db, [item.id], fail_fast=False)

        db.refresh(batch)
        log = db.scalars(select(OperationLog).order_by(OperationLog.id)).first()
        assert isinstance(batch, ExecutionBatch)
        assert batch.success_count == 1
        assert log is not None
        assert log.operation_type == "rename"
        assert log.status == "success"
        assert pan.get_path("f1") == "/下载/新名.mkv"
