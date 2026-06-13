import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.database import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture
def client():
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
