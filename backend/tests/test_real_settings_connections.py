import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.settings as settings_api
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


def test_test_115_uses_configured_cookie_and_real_client_hook(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakePan115:
        def __init__(self, cookie: str) -> None:
            self.cookie = cookie

        def test_connection(self) -> bool:
            return self.cookie == "UID=abc; CID=def"

    monkeypatch.setattr(settings_api, "PAN115_CLIENT_CLASS", FakePan115)
    client.put(
        "/api/settings",
        json={
            "pan115_cookie": "UID=abc; CID=def",
            "tmdb_language": "zh-CN",
            "default_source_dir": "100",
            "default_target_dir": "200",
            "default_recycle_dir": "300",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )

    response = client.post("/api/settings/test-115")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "message": "115 连接成功"}


def test_test_tmdb_uses_configured_api_key_and_real_client_hook(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakeTmdb:
        def __init__(self, api_key: str, language: str) -> None:
            self.api_key = api_key
            self.language = language

        def search_movie(self, title: str, year: int | None) -> list:
            assert self.api_key == "tmdb-secret-key"
            assert self.language == "zh-CN"
            assert title == "test"
            assert year is None
            return []

    monkeypatch.setattr(settings_api, "TMDB_CLIENT_CLASS", FakeTmdb)
    client.put(
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

    response = client.post("/api/settings/test-tmdb")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "message": "TMDB 连接成功"}
