import httpx
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


def save_tmdb_key(client: TestClient) -> None:
    response = client.put(
        "/api/settings",
        json={
            "tmdb_api_key": "tmdb-secret-key",
            "tmdb_language": "zh-CN",
            "default_source_dir": "100",
            "default_target_dir": "200",
            "default_recycle_dir": "300",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )
    assert response.status_code == 200


def test_test_tmdb_reports_network_error_detail(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class BrokenTmdb:
        def __init__(self, api_key: str, language: str) -> None:
            self.api_key = api_key
            self.language = language

        def search_movie(self, title: str, year: int | None) -> list:
            request = httpx.Request("GET", "https://api.themoviedb.org/3/search/movie")
            raise httpx.ConnectError("network unreachable", request=request)

    import app.api.settings as settings_api

    monkeypatch.setattr(settings_api, "TMDB_CLIENT_CLASS", BrokenTmdb)
    save_tmdb_key(client)

    response = client.post("/api/settings/test-tmdb")

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "ConnectError" in response.json()["message"]


def test_test_tmdb_reports_http_status_detail(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class UnauthorizedTmdb:
        def __init__(self, api_key: str, language: str) -> None:
            self.api_key = api_key
            self.language = language

        def search_movie(self, title: str, year: int | None) -> list:
            request = httpx.Request("GET", "https://api.themoviedb.org/3/search/movie")
            response = httpx.Response(401, request=request)
            raise httpx.HTTPStatusError("unauthorized", request=request, response=response)

    import app.api.settings as settings_api

    monkeypatch.setattr(settings_api, "TMDB_CLIENT_CLASS", UnauthorizedTmdb)
    save_tmdb_key(client)

    response = client.post("/api/settings/test-tmdb")

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "HTTP 401" in response.json()["message"]
