import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
                "流浪地球 2019 2160p.mkv",
                "/下载/流浪地球 2019 2160p.mkv",
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
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_scan_uses_injected_real_clients_and_persists_tmdb_match(client: TestClient):
    rule_response = client.post(
        "/api/rules",
        json={
            "name": "movie-year",
            "media_type": "movie",
            "pattern": r"(?P<title>.+?) (?P<year>20\d{2}) (?P<resolution>\d{3,4}p)",
            "template": "/电影/{title_cn} ({year})/{title_cn} ({year}) - {resolution}.{ext}",
            "priority": 10,
            "enabled": True,
        },
    )
    assert rule_response.status_code == 200

    scan_response = client.post(
        "/api/scans",
        json={
            "source_dir": "src",
            "target_dir": "/电影",
            "media_type": "movie",
            "recursive": True,
        },
    )
    assert scan_response.status_code == 200
    scan = scan_response.json()
    assert scan["file_count"] == 1

    items_response = client.get(f"/api/scans/{scan['id']}/items")
    assert items_response.status_code == 200
    items = items_response.json()
    assert items[0]["tmdb_title"] == "流浪地球"
