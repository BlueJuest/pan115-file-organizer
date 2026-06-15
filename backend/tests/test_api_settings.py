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


def test_settings_round_trip_masks_secrets(client: TestClient):
    response = client.put(
        "/api/settings",
        json={
            "pan115_cookie": "UID=abc; CID=def; SEID=secret-value",
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
    body = response.json()
    assert body["pan115_cookie_masked"].startswith("UID=")
    assert "secret-value" not in body["pan115_cookie_masked"]
    assert body["tmdb_api_key_masked"].startswith("tmdb")
    assert "secret-key" not in body["tmdb_api_key_masked"]
    assert body["default_source_dir"] == "100"


def test_settings_masks_short_secrets(client: TestClient):
    response = client.put(
        "/api/settings",
        json={
            "pan115_cookie": "abcde",
            "tmdb_api_key": "abcdefgh",
            "tmdb_language": "zh-CN",
            "default_source_dir": "100",
            "default_target_dir": "200",
            "default_recycle_dir": "300",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pan115_cookie_masked"] != "abcde"
    assert "*" in body["pan115_cookie_masked"]
    assert body["tmdb_api_key_masked"] != "abcdefgh"
    assert "*" in body["tmdb_api_key_masked"]


def test_settings_update_keeps_existing_secrets_when_omitted(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakePan115:
        def __init__(self, cookie: str) -> None:
            self.cookie = cookie

        def test_connection(self) -> bool:
            return bool(self.cookie)

    class FakeTmdb:
        def __init__(self, api_key: str, language: str) -> None:
            self.api_key = api_key
            self.language = language

        def search_movie(self, title: str, year: int | None) -> list:
            return []

    import app.api.settings as settings_api

    monkeypatch.setattr(settings_api, "PAN115_CLIENT_CLASS", FakePan115)
    monkeypatch.setattr(settings_api, "TMDB_CLIENT_CLASS", FakeTmdb)
    response = client.put(
        "/api/settings",
        json={
            "pan115_cookie": "UID=abc; CID=def; SEID=secret-value",
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

    response = client.put(
        "/api/settings",
        json={
            "tmdb_language": "en-US",
            "default_source_dir": "101",
            "default_target_dir": "201",
            "default_recycle_dir": "301",
            "allow_delete_old_files": True,
            "recursive_scan": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tmdb_language"] == "en-US"
    assert body["default_source_dir"] == "101"

    response_115 = client.post("/api/settings/test-115")
    response_tmdb = client.post("/api/settings/test-tmdb")
    assert response_115.json()["ok"] is True
    assert response_tmdb.json()["ok"] is True


def test_settings_update_keeps_existing_secrets_when_empty_strings(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakePan115:
        def __init__(self, cookie: str) -> None:
            self.cookie = cookie

        def test_connection(self) -> bool:
            return bool(self.cookie)

    class FakeTmdb:
        def __init__(self, api_key: str, language: str) -> None:
            self.api_key = api_key
            self.language = language

        def search_movie(self, title: str, year: int | None) -> list:
            return []

    import app.api.settings as settings_api

    monkeypatch.setattr(settings_api, "PAN115_CLIENT_CLASS", FakePan115)
    monkeypatch.setattr(settings_api, "TMDB_CLIENT_CLASS", FakeTmdb)
    response = client.put(
        "/api/settings",
        json={
            "pan115_cookie": "UID=abc; CID=def; SEID=secret-value",
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

    response = client.put(
        "/api/settings",
        json={
            "pan115_cookie": "",
            "tmdb_api_key": "",
            "tmdb_language": "en-US",
            "default_source_dir": "101",
            "default_target_dir": "201",
            "default_recycle_dir": "301",
            "allow_delete_old_files": True,
            "recursive_scan": False,
        },
    )
    assert response.status_code == 200

    response_115 = client.post("/api/settings/test-115")
    response_tmdb = client.post("/api/settings/test-tmdb")
    assert response_115.json()["ok"] is True
    assert response_tmdb.json()["ok"] is True


def test_test_endpoints_return_not_configured_when_missing_keys(client: TestClient):
    response_115 = client.post("/api/settings/test-115")
    response_tmdb = client.post("/api/settings/test-tmdb")

    assert response_115.status_code == 200
    assert response_tmdb.status_code == 200
    assert response_115.json()["ok"] is False
    assert response_tmdb.json()["ok"] is False
    assert "未配置" in response_115.json()["message"]
    assert "未配置" in response_tmdb.json()["message"]
