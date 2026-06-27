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
        if dir_id == "0":
            return [
                RemoteFile("movies", "Movies", "/Movies", "0", True, 0),
                RemoteFile("f-root", "Loose 2024.mkv", "/Loose 2024.mkv", "0", False, 100),
            ]
        return [
            RemoteFile(
                "f1",
                "Avatar 2009 2160p.mkv",
                "/Downloads/Avatar 2009 2160p.mkv",
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
                19995,
                "movie",
                "Avatar",
                "Avatar",
                2009,
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
            "template": "/Movies/{title_cn} ({year})/{title_cn} ({year}) - {resolution}.{ext}",
            "priority": 10,
            "enabled": True,
        },
    )
    assert rule_response.status_code == 200

    scan_response = client.post(
        "/api/scans",
        json={
            "source_dir": "src",
            "target_dir": "/Movies",
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
    assert items[0]["tmdb_title"] == "Avatar"


def test_scan_renders_moviepilot_jinja_fields(client: TestClient):
    rule_response = client.post(
        "/api/rules",
        json={
            "name": "moviepilot-movie",
            "media_type": "movie",
            "pattern": r"(?P<title>.+?) (?P<year>20\d{2}) (?P<videoFormat>\d{3,4}p)",
            "template": "{{title}}{% if year %} ({{year}}){% endif %}/{{title}}{% if videoFormat %} - {{videoFormat}}{% endif %}{{fileExt}}",
            "priority": 10,
            "enabled": True,
        },
    )
    assert rule_response.status_code == 200

    scan_response = client.post(
        "/api/scans",
        json={
            "source_dir": "src",
            "target_dir": "/Movies",
            "media_type": "movie",
            "recursive": True,
        },
    )
    assert scan_response.status_code == 200

    scan = scan_response.json()
    items_response = client.get(f"/api/scans/{scan['id']}/items")
    assert items_response.status_code == 200
    items = items_response.json()
    assert items[0]["new_path"].endswith("/Movies/Avatar (2009)/Avatar - 2160p.mkv")


def test_directory_browser_lists_realtime_115_directory(client: TestClient):
    response = client.get("/api/directories?parent_id=0")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "movies",
            "name": "Movies",
            "path": "/Movies",
            "parent_id": "0",
            "is_dir": True,
        }
    ]
