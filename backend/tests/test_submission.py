import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.submissions as submissions_api
import app.models  # noqa: F401
from app.clients.share115 import Share115Client
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


def test_parse_submission_folder_name_extracts_title_year_and_tmdb_id():
    parsed = submissions_api.parse_submission_folder_name("Example Movie (2024) {tmdbid=1211650}")

    assert parsed.title == "Example Movie"
    assert parsed.year == 2024
    assert parsed.tmdb_id == 1211650


def test_tmdb_details_falls_back_to_english_overview_when_localized_overview_is_empty():
    from app.clients.tmdb import TmdbClient

    class FakeHttpClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def get(self, path: str, params: dict):
            self.calls.append((path, dict(params)))
            language = params["language"]
            return FakeResponse(
                {
                    "id": 1268609,
                    "title": "Localized Title" if language == "zh-CN" else "English Title",
                    "release_date": "2026-01-01",
                    "overview": "" if language == "zh-CN" else "English fallback overview.",
                    "poster_path": "/poster.jpg",
                    "backdrop_path": "/backdrop.jpg",
                    "vote_average": 7.2,
                    "genres": [{"name": "Romance"}, {"name": "Drama"}],
                }
            )

    class FakeResponse:
        def __init__(self, payload: dict) -> None:
            self.payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self.payload

    client = TmdbClient("key", "zh-CN")
    fake_http = FakeHttpClient()
    client.client = fake_http

    details = client.get_details(1268609, "movie")

    assert details is not None
    assert details.title_cn == "Localized Title"
    assert details.overview == "English fallback overview."
    assert details.backdrop_path == "/backdrop.jpg"
    assert fake_http.calls[1][1]["language"] == "en-US"


def test_share115_client_reads_public_share_without_constructing_login_client(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict] = []

    class FakeP115Client:
        def __init__(self) -> None:
            raise AssertionError("public share inspection must not start qrcode login")

        @staticmethod
        def share_snap(payload: dict):
            calls.append(payload)
            return {
                "data": {
                    "share_title": "Example Movie (2024) {tmdbid=123}",
                    "user_name": "Uploader Name",
                    "list": [{"name": "movie.mkv", "size": 1024, "is_dir": 0}],
                }
            }

    monkeypatch.setattr("p115client.P115Client", FakeP115Client)

    inspection = Share115Client().inspect_share("https://115.com/s/sw123456", "abcd")

    assert inspection.folder_name == "Example Movie (2024) {tmdbid=123}"
    assert inspection.total_size == 1024
    assert inspection.share_user == "Uploader Name"
    assert calls[0]["share_code"] == "sw123456"
    assert calls[0]["receive_code"] == "abcd"


def test_preview_submission_uses_tmdb_image_and_auto_douban(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakeShareClient:
        def inspect_share(self, share_url: str, receive_code: str | None):
            assert share_url == "https://115.com/s/example?password=abcd"
            return submissions_api.ShareInspection(
                folder_name="Example Movie (2024) {tmdbid=1211650}",
                total_size=4831838208,
                share_user="Uploader Name",
            )

    class FakeTmdb:
        def __init__(self, api_key: str, language: str) -> None:
            self.api_key = api_key
            self.language = language

        def get_details(self, tmdb_id: int, media_type: str):
            if media_type == "movie":
                return submissions_api.SubmissionMediaDetails(
                    tmdb_id=tmdb_id,
                    media_type="movie",
                    title="Example Movie",
                    original_title="Example Movie Original",
                    year=2024,
                    overview="A useful overview.",
                    poster_path="/poster.jpg",
                    backdrop_path="/backdrop.jpg",
                    vote_average=7.2,
                    genres=["Romance", "Drama"],
                )
            return None

    class FakeDouban:
        def search(self, title: str, year: int | None):
            assert title == "Example Movie"
            assert year == 2024

            class Match:
                rating = "8.1/10"
                url = "https://movie.douban.com/subject/654321/"

            return Match()

    monkeypatch.setattr(submissions_api, "SHARE_CLIENT_CLASS", FakeShareClient)
    monkeypatch.setattr(submissions_api, "TMDB_CLIENT_CLASS", FakeTmdb)
    monkeypatch.setattr(submissions_api, "DOUBAN_CLIENT_CLASS", FakeDouban)

    client.put(
        "/api/settings",
        json={
            "tmdb_api_key": "tmdb-key",
            "tmdb_language": "zh-CN",
            "default_source_dir": "0",
            "default_target_dir": "0",
            "default_recycle_dir": "0",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )

    response = client.post(
        "/api/submissions/preview",
        json={
            "share_url": "https://115.com/s/example?password=abcd",
            "quality": "1080p",
            "video_source": "WEB-DL/WEBRip",
            "subtitles": "Simplified Chinese",
            "custom_content": "Custom line [Team]",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["image_url"] == "https://image.tmdb.org/t/p/original/backdrop.jpg"
    assert body["image_base64"] == ""
    assert body["douban_rating"] == "8.1/10"
    assert body["douban_url"] == "https://movie.douban.com/subject/654321/"
    assert body["share_user"] == "Uploader Name"
    assert body["share_user_url"] == "https://t.me/MeiOvO"
    assert "<b>Example Movie (2024)</b>" in body["caption"]
    assert "<blockquote><b>Custom line [Team]</b></blockquote>" in body["caption"]
    assert "<blockquote>A useful overview.</blockquote>" in body["caption"]
    assert '<a href="https://movie.douban.com/subject/654321/">8.1/10</a>' in body["caption"]
    assert '<a href="https://t.me/MeiOvO">Uploader Name</a>' in body["caption"]


def test_preview_submission_omits_douban_when_auto_match_fails(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakeShareClient:
        def inspect_share(self, share_url: str, receive_code: str | None):
            return submissions_api.ShareInspection(
                folder_name="Example Show (2025) {tmdbid=222}",
                total_size=1024,
                share_user="",
            )

    class FakeTmdb:
        def __init__(self, api_key: str, language: str) -> None:
            pass

        def get_details(self, tmdb_id: int, media_type: str):
            if media_type == "tv":
                return submissions_api.SubmissionMediaDetails(
                    tmdb_id=tmdb_id,
                    media_type="tv",
                    title="Example Show",
                    year=2025,
                    overview="",
                    poster_path="/poster.jpg",
                    backdrop_path="",
                    vote_average=None,
                    genres=[],
                )
            return None

    class FakeDouban:
        def search(self, title: str, year: int | None):
            return None

    monkeypatch.setattr(submissions_api, "SHARE_CLIENT_CLASS", FakeShareClient)
    monkeypatch.setattr(submissions_api, "TMDB_CLIENT_CLASS", FakeTmdb)
    monkeypatch.setattr(submissions_api, "DOUBAN_CLIENT_CLASS", FakeDouban)

    client.put(
        "/api/settings",
        json={
            "tmdb_api_key": "tmdb-key",
            "tmdb_language": "zh-CN",
            "default_source_dir": "0",
            "default_target_dir": "0",
            "default_recycle_dir": "0",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )

    response = client.post(
        "/api/submissions/preview",
        json={
            "share_url": "https://115.com/s/example?password=abcd",
            "quality": "1080p",
            "video_source": "WEB-DL/WEBRip",
            "subtitles": "Simplified Chinese",
            "custom_content": "",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["douban_rating"] == ""
    assert body["douban_url"] == ""
    assert body["share_user"] == "MeiOvO"
    assert body["image_url"] == "https://image.tmdb.org/t/p/original/poster.jpg"
    assert "movie.douban.com" not in body["caption"]


def test_preview_submission_manual_tv_type_queries_only_tv(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    class FakeShareClient:
        def inspect_share(self, share_url: str, receive_code: str | None):
            return submissions_api.ShareInspection(
                folder_name="Example Show (2025) {tmdbid=222}",
                total_size=1024,
            )

    class FakeTmdb:
        def __init__(self, api_key: str, language: str) -> None:
            pass

        def get_details(self, tmdb_id: int, media_type: str):
            calls.append(media_type)
            if media_type == "tv":
                return submissions_api.SubmissionMediaDetails(
                    tmdb_id=tmdb_id,
                    media_type="tv",
                    title="Example Show",
                    year=2025,
                    poster_path="/poster.jpg",
                )
            return None

    class FakeDouban:
        def search(self, title: str, year: int | None):
            return None

    monkeypatch.setattr(submissions_api, "SHARE_CLIENT_CLASS", FakeShareClient)
    monkeypatch.setattr(submissions_api, "TMDB_CLIENT_CLASS", FakeTmdb)
    monkeypatch.setattr(submissions_api, "DOUBAN_CLIENT_CLASS", FakeDouban)

    client.put(
        "/api/settings",
        json={
            "tmdb_api_key": "tmdb-key",
            "tmdb_language": "zh-CN",
            "default_source_dir": "0",
            "default_target_dir": "0",
            "default_recycle_dir": "0",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )

    response = client.post(
        "/api/submissions/preview",
        json={
            "share_url": "https://115.com/s/example?password=abcd",
            "media_type": "tv",
        },
    )

    assert response.status_code == 200
    assert calls == ["tv"]
    assert response.json()["media"]["media_type"] == "tv"


def test_douban_parse_link2_result_without_rating_returns_unrated_match():
    from app.clients.douban import DoubanClient

    html = """
    <div class="result">
      <a href="https://www.douban.com/link2/?url=https%3A%2F%2Fmovie.douban.com%2Fsubject%2F36666710%2F&amp;query=x">
        派对浪客诸葛孔明 通往夏日索尼娅之路
      </a>
      <span>暂无评分</span>
      <span>2024</span>
    </div>
    """

    match = DoubanClient().parse_search_html(html, "派对浪客诸葛孔明 通往夏日索尼娅之路", 2024)

    assert match is not None
    assert match.rating == ""
    assert match.url == "https://movie.douban.com/subject/36666710/"


def test_caption_shows_unrated_douban_link_when_url_has_no_rating():
    media = submissions_api.SubmissionMediaDetails(
        tmdb_id=36666710,
        media_type="movie",
        title="派对浪客诸葛孔明 通往夏日索尼娅之路",
        year=2024,
    )
    payload = submissions_api.SubmissionPreviewRequest(share_url="https://115.com/s/example")

    caption = submissions_api._caption(
        media,
        payload,
        "1GB",
        "",
        "https://movie.douban.com/subject/36666710/",
        "MeiOvO",
    )

    assert '豆瓣：<a href="https://movie.douban.com/subject/36666710/">暂无评分</a>' in caption


def test_publish_submission_sends_tmdb_image_url_to_telegram(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    sent: dict[str, object] = {}

    class FakeTelegramClient:
        def __init__(self, bot_token: str, channel_id: str) -> None:
            sent["bot_token"] = bot_token
            sent["channel_id"] = channel_id

        def send_photo(self, image: str, caption: str) -> str:
            sent["image"] = image
            sent["caption"] = caption
            return "42"

    monkeypatch.setattr(submissions_api, "TELEGRAM_CLIENT_CLASS", FakeTelegramClient)

    client.put(
        "/api/settings",
        json={
            "telegram_bot_token": "token-123",
            "telegram_channel_id": "-1001234567890",
            "tmdb_language": "zh-CN",
            "default_source_dir": "0",
            "default_target_dir": "0",
            "default_recycle_dir": "0",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )

    response = client.post(
        "/api/submissions/publish",
        json={"image_url": "https://image.tmdb.org/t/p/original/backdrop.jpg", "caption": "Example"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True, "message": "Telegram 推送成功", "telegram_message_id": "42"}
    assert sent["image"] == "https://image.tmdb.org/t/p/original/backdrop.jpg"

    logs_response = client.get("/api/telegram-push-logs")

    assert logs_response.status_code == 200
    logs = logs_response.json()["items"]
    assert len(logs) == 1
    assert logs[0]["status"] == "success"
    assert logs[0]["telegram_message_id"] == "42"
    assert logs[0]["telegram_channel_id"] == "-1001234567890"
    assert logs[0]["caption"] == "Example"
    assert logs[0]["image_url"] == "https://image.tmdb.org/t/p/original/backdrop.jpg"


def test_publish_submission_uses_environment_telegram_config_when_database_is_empty(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    sent: dict[str, object] = {}

    class FakeTelegramClient:
        def __init__(self, bot_token: str, channel_id: str) -> None:
            sent["bot_token"] = bot_token
            sent["channel_id"] = channel_id

        def send_photo(self, image: str, caption: str) -> str:
            return "77"

    class FakeSettings:
        telegram_bot_token = "env-token"
        telegram_channel_id = "env-channel"

    monkeypatch.setattr(submissions_api, "TELEGRAM_CLIENT_CLASS", FakeTelegramClient)
    monkeypatch.setattr(submissions_api, "get_settings", lambda: FakeSettings())

    response = client.post(
        "/api/submissions/publish",
        json={"image_url": "https://image.tmdb.org/t/p/original/backdrop.jpg", "caption": "Example"},
    )

    assert response.status_code == 200
    assert response.json()["telegram_message_id"] == "77"
    assert sent["bot_token"] == "env-token"
    assert sent["channel_id"] == "env-channel"


def test_publish_submission_records_failed_telegram_push(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    class FakeTelegramClient:
        def __init__(self, bot_token: str, channel_id: str) -> None:
            pass

        def send_photo(self, image: str, caption: str) -> str:
            raise RuntimeError("Telegram send failed")

    monkeypatch.setattr(submissions_api, "TELEGRAM_CLIENT_CLASS", FakeTelegramClient)

    client.put(
        "/api/settings",
        json={
            "telegram_bot_token": "token-123",
            "telegram_channel_id": "-1001234567890",
            "tmdb_language": "zh-CN",
            "default_source_dir": "0",
            "default_target_dir": "0",
            "default_recycle_dir": "0",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )

    response = client.post(
        "/api/submissions/publish",
        json={"image_url": "https://image.tmdb.org/t/p/original/backdrop.jpg", "caption": "Failed log"},
    )

    assert response.status_code == 400
    logs = client.get("/api/telegram-push-logs").json()["items"]
    assert len(logs) == 1
    assert logs[0]["status"] == "failed"
    assert logs[0]["error_message"] == "Telegram send failed"
    assert logs[0]["caption"] == "Failed log"


def test_telegram_push_logs_can_be_filtered_deleted_and_resent(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    sent: list[tuple[str, str, str]] = []

    class FakeTelegramClient:
        def __init__(self, bot_token: str, channel_id: str) -> None:
            self.channel_id = channel_id

        def send_photo(self, image: str, caption: str) -> str:
            sent.append((self.channel_id, image, caption))
            return str(100 + len(sent))

    monkeypatch.setattr(submissions_api, "TELEGRAM_CLIENT_CLASS", FakeTelegramClient)

    client.put(
        "/api/settings",
        json={
            "telegram_bot_token": "token-123",
            "telegram_channel_id": "-1001234567890",
            "tmdb_language": "zh-CN",
            "default_source_dir": "0",
            "default_target_dir": "0",
            "default_recycle_dir": "0",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )
    client.post(
        "/api/submissions/publish",
        json={"image_url": "https://image.tmdb.org/t/p/original/a.jpg", "caption": "First Alpha"},
    )
    client.post(
        "/api/submissions/publish",
        json={"image_url": "https://image.tmdb.org/t/p/original/b.jpg", "caption": "Second Beta"},
    )

    filtered_response = client.get("/api/telegram-push-logs", params={"keyword": "Alpha", "status": "success"})

    assert filtered_response.status_code == 200
    filtered = filtered_response.json()
    assert filtered["total"] == 1
    source_log = filtered["items"][0]
    assert source_log["caption"] == "First Alpha"

    resend_response = client.post(f"/api/telegram-push-logs/{source_log['id']}/resend")

    assert resend_response.status_code == 200
    resent = resend_response.json()
    assert resent["ok"] is True
    assert resent["telegram_message_id"] == "103"
    assert sent[-1] == ("-1001234567890", "https://image.tmdb.org/t/p/original/a.jpg", "First Alpha")

    logs_after_resend = client.get("/api/telegram-push-logs").json()["items"]
    resend_log = next(item for item in logs_after_resend if item["telegram_message_id"] == "103")
    assert resend_log["resent_from_id"] == source_log["id"]

    delete_response = client.delete(f"/api/telegram-push-logs/{source_log['id']}")

    assert delete_response.status_code == 200
    remaining_ids = {item["id"] for item in client.get("/api/telegram-push-logs").json()["items"]}
    assert source_log["id"] not in remaining_ids


def test_telegram_client_sends_photo_url_as_html(monkeypatch: pytest.MonkeyPatch):
    from app.clients.telegram import TelegramClient

    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"ok": True, "result": {"message_id": 99}}

    def fake_post(url: str, data: dict, timeout: int):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    message_id = TelegramClient("token", "channel").send_photo(
        "https://image.tmdb.org/t/p/original/backdrop.jpg",
        '<a href="https://115.com/s/x">115网盘</a>',
    )

    assert message_id == "99"
    assert captured["data"] == {
        "chat_id": "channel",
        "photo": "https://image.tmdb.org/t/p/original/backdrop.jpg",
        "caption": '<a href="https://115.com/s/x">115网盘</a>',
        "parse_mode": "HTML",
    }
