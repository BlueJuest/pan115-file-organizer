from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.execute as execute_api
from app.core.database import get_db
from app.main import app
from app.clients.protocols import OperationResult
from app.models import OperationLog, PreviewItem, ScanBatch
from app.models.base import Base
from app.services.client_factory import ClientConfigError
from app.services.executor import Executor


class RecordingPan:
    def __init__(self, rename_results: list[OperationResult] | None = None) -> None:
        self.calls: list[tuple] = []
        self.rename_results = rename_results or []

    def ensure_dir_path(self, path: str, root_id: str = "0") -> str:
        self.calls.append(("ensure_dir_path", path, root_id))
        return "target-dir"

    def rename(self, file_id: str, new_name: str) -> OperationResult:
        self.calls.append(("rename", file_id, new_name))
        if self.rename_results:
            return self.rename_results.pop(0)
        return OperationResult(True)

    def move(self, file_id: str, target_dir_id: str) -> OperationResult:
        self.calls.append(("move", file_id, target_dir_id))
        return OperationResult(True)

    def delete(self, file_id: str) -> OperationResult:
        self.calls.append(("delete", file_id))
        return OperationResult(True)


def make_db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def add_preview_item(
    db: Session,
    *,
    file_id: str = "f1",
    original_path: str = "/下载/旧名.mkv",
    new_path: str = "/电影/流浪地球 (2019)/新名.mkv",
    final_action: str = "rename_move",
) -> PreviewItem:
    scan_batch = ScanBatch(source_dir="/下载", target_dir="/电影")
    db.add(scan_batch)
    db.flush()
    item = PreviewItem(
        scan_batch_id=scan_batch.id,
        file_id=file_id,
        original_path=original_path,
        new_path=new_path,
        final_action=final_action,
    )
    db.add(item)
    db.commit()
    return item


def test_executor_rename_move_creates_dir_then_renames_then_moves():
    engine = make_db()
    pan = RecordingPan()

    with Session(engine) as db:
        item = add_preview_item(db)

        batch = Executor(pan).execute(db, [item.id], fail_fast=False)

        assert batch.success_count == 1
        assert pan.calls == [
            ("ensure_dir_path", "/电影/流浪地球 (2019)", "0"),
            ("rename", "f1", "新名.mkv"),
            ("move", "f1", "target-dir"),
        ]


def test_executor_delete_old_is_not_reversible():
    engine = make_db()
    pan = RecordingPan()

    with Session(engine) as db:
        item = add_preview_item(db, final_action="delete_old")

        batch = Executor(pan).execute(db, [item.id], fail_fast=False)

        log = db.scalars(select(OperationLog)).one()
        assert batch.success_count == 1
        assert pan.calls == [("delete", "f1")]
        assert log.operation_type == "delete_old"
        assert log.reversible == 0

def test_executor_continues_after_failed_item():
    engine = make_db()
    pan = RecordingPan([OperationResult(False, "rename failed"), OperationResult(True)])

    with Session(engine) as db:
        failed_item = add_preview_item(
            db,
            file_id="f1",
            original_path="/下载/旧1.mkv",
            new_path="/下载/新1.mkv",
            final_action="rename",
        )
        success_item = add_preview_item(
            db,
            file_id="f2",
            original_path="/下载/旧2.mkv",
            new_path="/下载/新2.mkv",
            final_action="rename",
        )

        batch = Executor(pan).execute(db, [failed_item.id, success_item.id], fail_fast=False)

        assert batch.failed_count == 1
        assert batch.success_count == 1
        assert pan.calls == [
            ("rename", "f1", "新1.mkv"),
            ("rename", "f2", "新2.mkv"),
        ]


def test_executor_skips_missing_remote_file_and_continues():
    engine = make_db()
    pan = RecordingPan([OperationResult(False, "文件不存在"), OperationResult(True)])

    with Session(engine) as db:
        missing_item = add_preview_item(
            db,
            file_id="missing",
            original_path="/下载/缺失.mkv",
            new_path="/下载/缺失-新名.mkv",
            final_action="rename",
        )
        success_item = add_preview_item(
            db,
            file_id="f2",
            original_path="/下载/旧2.mkv",
            new_path="/下载/新2.mkv",
            final_action="rename",
        )

        batch = Executor(pan).execute(db, [missing_item.id, success_item.id], fail_fast=True)

        missing_log = db.scalars(
            select(OperationLog).where(OperationLog.preview_item_id == missing_item.id)
        ).one()
        assert batch.skipped_count == 1
        assert batch.failed_count == 0
        assert batch.success_count == 1
        assert missing_log.status == "skipped"
        assert missing_log.error_message == "文件不存在"
        assert pan.calls == [
            ("rename", "missing", "缺失-新名.mkv"),
            ("rename", "f2", "新2.mkv"),
        ]


class FakeExecutionFactory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def pan115(self) -> RecordingPan:
        return RecordingPan()


class FailingExecutionFactory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def pan115(self) -> RecordingPan:
        raise ClientConfigError("未配置 115 Cookie")


def make_client(monkeypatch, factory_class):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(execute_api, "CLIENT_FACTORY_CLASS", factory_class)
    test_client = TestClient(app)
    return test_client, engine


def test_create_execution_uses_injected_client_factory(monkeypatch):
    client, engine = make_client(monkeypatch, FakeExecutionFactory)
    try:
        response = client.post("/api/executions", json={"preview_item_ids": [], "fail_fast": False})
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

    assert response.status_code == 200
    assert response.json()["item_count"] == 0


def test_create_execution_returns_400_for_client_config_error(monkeypatch):
    client, engine = make_client(monkeypatch, FailingExecutionFactory)
    try:
        response = client.post("/api/executions", json={"preview_item_ids": [], "fail_fast": False})
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

    assert response.status_code == 400
    assert response.json()["detail"] == "未配置 115 Cookie"
