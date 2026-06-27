import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.execute as execute_api
import app.api.scan as scan_api
import app.models  # noqa: F401
from app.clients.protocols import RemoteFile, TmdbCandidate
from app.core.database import get_db
from app.main import app
from app.models.base import Base


class FakePan115:
    def list_dir(self, dir_id: str) -> list[RemoteFile]:
        return [
            RemoteFile(
                "f1",
                "流浪地球 2019 2160p WEB-DL.mkv",
                "/下载/流浪地球 2019 2160p WEB-DL.mkv",
                dir_id,
                False,
                100,
            )
        ]

    def list_dir_recursive(self, dir_id: str) -> list[RemoteFile]:
        return self.list_dir(dir_id)


class FakeTmdb:
    def search_movie(self, title: str, year: int | None) -> list[TmdbCandidate]:
        return [
            TmdbCandidate(
                535167,
                "movie",
                "流浪地球",
                "The Wandering Earth",
                2019,
                0.95,
            )
        ]

    def search_tv(self, title: str, year: int | None) -> list[TmdbCandidate]:
        return []


class FakeFactory:
    def __init__(self, db):
        self.db = db

    def pan115(self) -> FakePan115:
        return FakePan115()

    def tmdb(self) -> FakeTmdb:
        return FakeTmdb()


@pytest.fixture
def client(monkeypatch):
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
    monkeypatch.setattr(scan_api, "CLIENT_FACTORY_CLASS", FakeFactory)
    monkeypatch.setattr(execute_api, "CLIENT_FACTORY_CLASS", FakeFactory)
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_scan_execute_and_rollback_plan_flow(client: TestClient):
    rule_response = client.post(
        "/api/rules",
        json={
            "name": "movie-year",
            "media_type": "movie",
            "pattern": r"(?P<title>.+?)[ ._-]+(?P<year>20\d{2})[ ._-]+(?P<resolution>2160p|1080p)",
            "template": "/电影/{title} ({year})/{title} ({year}) - {resolution}.{ext}",
            "priority": 10,
            "enabled": True,
            "sample_input": "流浪地球 2019 2160p WEB-DL.mkv",
            "sample_output": "/电影/流浪地球 (2019)/流浪地球 (2019) - 2160p.mkv",
        },
    )
    assert rule_response.status_code == 200

    scan_response = client.post(
        "/api/scans",
        json={
            "source_dir": "src",
            "target_dir": "/电影",
            "media_type": "movie",
            "recursive": False,
        },
    )
    assert scan_response.status_code == 200
    scan_id = scan_response.json()["id"]

    items_response = client.get(f"/api/scans/{scan_id}/items")
    assert items_response.status_code == 200
    assert isinstance(items_response.json(), list)

    execution_response = client.post(
        "/api/executions",
        json={"preview_item_ids": [], "fail_fast": False},
    )
    assert execution_response.status_code == 200
    execution_id = execution_response.json()["id"]

    rollback_plan_response = client.post(f"/api/executions/{execution_id}/rollback-plan")
    assert rollback_plan_response.status_code == 200
    rollback_plan = rollback_plan_response.json()
    assert rollback_plan["execution_batch_id"] == execution_id
    assert "items" in rollback_plan
