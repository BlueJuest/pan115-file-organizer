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


def test_create_rule_and_test_rule(client: TestClient):
    response = client.post(
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

    assert response.status_code == 200
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "movie-year"
    assert body["enabled"] is True
    assert body["hit_count"] == 0

    list_response = client.get("/api/rules")
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "movie-year"

    test_response = client.post(
        "/api/rules/test",
        json={
            "media_type": "movie",
            "pattern": body["pattern"],
            "template": body["template"],
            "priority": body["priority"],
            "enabled": body["enabled"],
            "sample_input": body["sample_input"],
        },
    )

    assert test_response.status_code == 200
    test_body = test_response.json()
    assert test_body["matched"] is True
    assert test_body["fields"]["title"] == "流浪地球"
    assert test_body["output"] == "/电影/流浪地球 (2019)/流浪地球 (2019) - 2160p.mkv"
    assert test_body["error"] == ""


def test_create_quality_profile(client: TestClient):
    response = client.post(
        "/api/quality-profiles",
        json={
            "name": "默认洗版策略",
            "resolution_weight": 45,
            "source_weight": 20,
            "video_codec_weight": 15,
            "audio_codec_weight": 10,
            "size_weight": 5,
            "subtitle_weight": 5,
            "min_upgrade_delta": 12,
            "default_old_file_action": "move_to_recycle",
            "resolution_order": "2160p,1080p,720p",
            "source_order": "BluRay,WEB-DL,WEBRip,HDTV",
            "video_codec_order": "H.265,HEVC,H.264,AVC",
            "audio_codec_order": "TrueHD,DTS-HD,DDP,DD,AAC",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "默认洗版策略"
    assert body["resolution_weight"] == 45
    assert body["min_upgrade_delta"] == 12

    list_response = client.get("/api/quality-profiles")
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "默认洗版策略"
