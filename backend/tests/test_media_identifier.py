import pytest

from app.clients.mock_pan115 import MockPan115Client
from app.clients.protocols import RemoteFile, TmdbCandidate
from app.clients.tmdb import TmdbClient
from app.services.media_identifier import MediaIdentifier, ParsedFileInfo


class FakeTmdbClient:
    def search_movie(self, title: str, year: int | None):
        assert title == "流浪地球"
        assert year == 2019
        return [
            TmdbCandidate(
                tmdb_id=535167,
                media_type="movie",
                title_cn="流浪地球",
                title_original="The Wandering Earth",
                year=2019,
                confidence=0.95,
            )
        ]

    def search_tv(self, title: str, year: int | None):
        return []

    def get_details(self, tmdb_id: int, media_type: str):
        return None


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class RecordingHttpClient:
    def __init__(self, payloads: dict[str, dict]):
        self.payloads = payloads
        self.calls: list[tuple[str, dict]] = []

    def get(self, path: str, params: dict):
        self.calls.append((path, params))
        return FakeResponse(self.payloads[path])


def test_media_identifier_uses_tmdb_candidate():
    identifier = MediaIdentifier(tmdb_client=FakeTmdbClient())
    parsed = ParsedFileInfo(
        title="流浪地球",
        year=2019,
        media_type="movie",
        fields={"title": "流浪地球", "year": "2019"},
    )

    result = identifier.identify(parsed)

    assert result.status == "recognized"
    assert result.tmdb_id == 535167
    assert result.title_cn == "流浪地球"
    assert result.confidence == 0.95


def test_media_identifier_falls_back_when_tmdb_fails():
    class BrokenTmdbClient(FakeTmdbClient):
        def search_movie(self, title: str, year: int | None):
            raise RuntimeError("network down")

    identifier = MediaIdentifier(tmdb_client=BrokenTmdbClient())
    parsed = ParsedFileInfo(
        title="未知电影",
        year=2024,
        media_type="movie",
        fields={"title": "未知电影"},
    )

    result = identifier.identify(parsed)

    assert result.status == "tmdb_failed"
    assert result.title_cn == "未知电影"
    assert result.error == "network down"


def test_media_identifier_reports_tmdb_value_error_as_tmdb_failed():
    class BadPayloadTmdbClient(FakeTmdbClient):
        def search_movie(self, title: str, year: int | None):
            raise ValueError("bad payload")

    identifier = MediaIdentifier(tmdb_client=BadPayloadTmdbClient())
    parsed = ParsedFileInfo(title="坏电影", year=2024, media_type="movie")

    result = identifier.identify(parsed)

    assert result.status == "tmdb_failed"
    assert "bad payload" in result.error


def test_mock_pan115_rename_updates_path():
    client = MockPan115Client(
        files=[RemoteFile("1", "旧名.mkv", "/电影/旧名.mkv", "2", False, size=1024), RemoteFile("2", "电影", "/电影", "0", True)]
    )

    result = client.rename("1", "新名.mkv")

    assert result.ok is True
    assert client.get_path("1") == "/电影/新名.mkv"


def test_mock_pan115_rename_preserves_directory_when_parent_is_missing():
    client = MockPan115Client(
        files=[RemoteFile("f1", "旧名.mkv", "/下载/旧名.mkv", "src", False, 1)]
    )

    result = client.rename("f1", "新名.mkv")

    assert result.ok is True
    assert client.get_path("f1") == "/下载/新名.mkv"


def test_mock_pan115_rejects_invalid_rename_names_without_changing_path():
    client = MockPan115Client(files=[RemoteFile("file", "旧名.mkv", "/旧名.mkv", "0", False)])

    empty_result = client.rename("file", "")
    slash_result = client.rename("file", "a/b.mkv")
    backslash_result = client.rename("file", "a\\b.mkv")

    assert empty_result.ok is False
    assert slash_result.ok is False
    assert backslash_result.ok is False
    assert client.get_path("file") == "/旧名.mkv"


def test_mock_pan115_rejects_rename_to_existing_sibling_name():
    client = MockPan115Client(
        files=[
            RemoteFile("A", "A.mkv", "/A.mkv", "0", False, 1),
            RemoteFile("B", "B.mkv", "/B.mkv", "0", False, 1),
        ]
    )

    result = client.rename("B", "A.mkv")

    assert result.ok is False
    assert "目标已存在" in result.message
    assert client.get_path("A") == "/A.mkv"
    assert client.get_path("B") == "/B.mkv"


def test_mock_pan115_move_directory_refreshes_child_paths():
    client = MockPan115Client(
        files=[
            RemoteFile("10", "剧集", "/剧集", "0", True),
            RemoteFile("11", "S01", "/剧集/S01", "10", True),
            RemoteFile("12", "E01.mkv", "/剧集/S01/E01.mkv", "11", False),
            RemoteFile("20", "归档", "/归档", "0", True),
        ]
    )

    result = client.move("10", "20")

    assert result.ok is True
    assert client.get_path("10") == "/归档/剧集"
    assert client.get_path("11") == "/归档/剧集/S01"
    assert client.get_path("12") == "/归档/剧集/S01/E01.mkv"


def test_mock_pan115_rejects_move_to_self_and_descendant_without_breaking_tree():
    client = MockPan115Client(
        files=[
            RemoteFile("10", "剧集", "/剧集", "0", True),
            RemoteFile("11", "S01", "/剧集/S01", "10", True),
            RemoteFile("12", "E01.mkv", "/剧集/S01/E01.mkv", "11", False),
        ]
    )

    self_result = client.move("10", "10")
    descendant_result = client.move("10", "11")

    assert self_result.ok is False
    assert descendant_result.ok is False
    assert client.get_path("10") == "/剧集"
    assert client.get_path("11") == "/剧集/S01"
    assert client.get_path("12") == "/剧集/S01/E01.mkv"


def test_mock_pan115_rejects_move_when_target_has_same_name():
    client = MockPan115Client(
        files=[
            RemoteFile("src", "来源", "/来源", "0", True),
            RemoteFile("dst", "目标", "/目标", "0", True),
            RemoteFile("file", "A.mkv", "/来源/A.mkv", "src", False, 1),
            RemoteFile("existing", "A.mkv", "/目标/A.mkv", "dst", False, 1),
        ]
    )

    result = client.move("file", "dst")

    assert result.ok is False
    assert "目标已存在" in result.message
    assert client.get_path("file") == "/来源/A.mkv"
    assert client.list_dir("src")[0].file_id == "file"
    assert client.get_path("existing") == "/目标/A.mkv"


def test_mock_pan115_mkdir_creates_directory_under_parent():
    client = MockPan115Client()

    new_dir = client.mkdir("0", "新目录")

    assert new_dir.name == "新目录"
    assert new_dir.path == "/新目录"
    assert new_dir.dir_id != "0"
    root_children = client.list_dir("0")
    assert len(root_children) == 1
    assert root_children[0].file_id == new_dir.dir_id
    assert root_children[0].name == "新目录"
    assert root_children[0].is_dir is True
    assert client.get_path(new_dir.dir_id) == "/新目录"


def test_mock_pan115_rejects_invalid_mkdir_parent():
    client = MockPan115Client(files=[RemoteFile("1", "电影.mkv", "/电影.mkv", "0", False)])

    with pytest.raises(ValueError):
        client.mkdir("missing", "新目录")
    with pytest.raises(ValueError):
        client.mkdir("1", "新目录")


def test_mock_pan115_rejects_invalid_mkdir_names_without_creating_nodes():
    client = MockPan115Client()

    with pytest.raises(ValueError):
        client.mkdir("0", "")
    with pytest.raises(ValueError):
        client.mkdir("0", "a/b")
    with pytest.raises(ValueError):
        client.mkdir("0", "a\\b")

    assert client.list_dir("0") == []


def test_mock_pan115_rejects_mkdir_when_sibling_name_exists():
    client = MockPan115Client(files=[RemoteFile("10", "剧集", "/剧集", "0", True)])

    with pytest.raises(ValueError, match="目标已存在"):
        client.mkdir("0", "剧集")

    matching_children = [child for child in client.list_dir("0") if child.name == "剧集"]
    assert len(matching_children) == 1
    assert matching_children[0].file_id == "10"


def test_mock_pan115_delete_removes_directory_descendants_and_keeps_unrelated_nodes():
    client = MockPan115Client(
        files=[
            RemoteFile("10", "剧集", "/剧集", "0", True),
            RemoteFile("11", "S01", "/剧集/S01", "10", True),
            RemoteFile("12", "E01.mkv", "/剧集/S01/E01.mkv", "11", False),
            RemoteFile("20", "电影", "/电影", "0", True),
            RemoteFile("21", "电影.mkv", "/电影/电影.mkv", "20", False),
        ]
    )

    result = client.delete("10")

    assert result.ok is True
    assert client.get_path("10") == ""
    assert client.get_path("11") == ""
    assert client.get_path("12") == ""
    assert client.get_path("20") == "/电影"
    assert client.get_path("21") == "/电影/电影.mkv"


def test_mock_pan115_delete_missing_fails_and_get_path_missing_returns_empty():
    client = MockPan115Client()

    result = client.delete("missing")

    assert result.ok is False
    assert client.get_path("missing") == ""


def test_mock_pan115_rejects_root_mutations():
    client = MockPan115Client()

    rename_result = client.rename("0", "root2")

    assert rename_result.ok is False
    assert client.get_path("0") == "/"
    assert client.move("0", "0").ok is False
    assert client.delete("0").ok is False


def test_tmdb_client_maps_movie_and_tv_fields_without_real_network():
    movie_payload = {
        "results": [
            {
                "id": 1,
                "title": "流浪地球",
                "original_title": "The Wandering Earth",
                "release_date": "2019-02-05",
                "overview": "科幻电影",
                "poster_path": "/movie.jpg",
            }
        ]
    }
    tv_payload = {
        "results": [
            {
                "id": 2,
                "name": "三体",
                "original_name": "Three-Body",
                "first_air_date": "2023-01-15",
                "overview": "科幻剧集",
                "poster_path": "/tv.jpg",
            }
        ]
    }
    client = TmdbClient(api_key="key")
    client.client = RecordingHttpClient({"/search/movie": movie_payload, "/search/tv": tv_payload})

    movie = client.search_movie("流浪地球", 2019)[0]
    tv = client.search_tv("三体", 2023)[0]

    assert movie.tmdb_id == 1
    assert movie.media_type == "movie"
    assert movie.title_cn == "流浪地球"
    assert movie.title_original == "The Wandering Earth"
    assert movie.year == 2019
    assert movie.overview == "科幻电影"
    assert movie.poster_path == "/movie.jpg"
    assert tv.tmdb_id == 2
    assert tv.media_type == "tv"
    assert tv.title_cn == "三体"
    assert tv.title_original == "Three-Body"
    assert tv.year == 2023
    assert tv.overview == "科幻剧集"
    assert tv.poster_path == "/tv.jpg"


def test_tmdb_search_confidence_prefers_title_and_year_over_high_rating():
    payload = {
        "results": [
            {
                "id": 10,
                "title": "错误电影",
                "original_title": "Wrong Movie",
                "release_date": "2024-01-01",
                "vote_average": 9.9,
            },
            {
                "id": 20,
                "title": "流浪地球",
                "original_title": "The Wandering Earth",
                "release_date": "2019-02-05",
                "vote_average": 1.0,
            },
        ]
    }
    client = TmdbClient(api_key="key")
    client.client = RecordingHttpClient({"/search/movie": payload})

    candidates = client.search_movie("流浪地球", 2019)

    assert candidates[1].confidence > candidates[0].confidence
    assert candidates[1].confidence >= 0.75


def test_tmdb_get_details_rejects_invalid_media_type():
    client = TmdbClient(api_key="key")

    with pytest.raises(ValueError):
        client.get_details(1, "documentary")


def test_media_identifier_no_client_fallback():
    result = MediaIdentifier().identify(ParsedFileInfo("标题", 2024, "movie"))

    assert result.status == "no_tmdb_client"
    assert result.title_cn == "标题"
    assert result.year == 2024


def test_media_identifier_empty_candidates_fallback():
    class EmptyTmdbClient:
        def search_movie(self, title: str, year: int | None):
            return []

        def search_tv(self, title: str, year: int | None):
            return []

        def get_details(self, tmdb_id: int, media_type: str):
            return None

    result = MediaIdentifier(EmptyTmdbClient()).identify(ParsedFileInfo("标题", 2024, "movie"))

    assert result.status == "not_recognized"
    assert result.title_cn == "标题"


def test_media_identifier_low_confidence_needs_confirm():
    class LowConfidenceTmdbClient:
        def search_movie(self, title: str, year: int | None):
            return [TmdbCandidate(1, "movie", "标题", "Title", 2024, 0.5)]

        def search_tv(self, title: str, year: int | None):
            return []

        def get_details(self, tmdb_id: int, media_type: str):
            return None

    result = MediaIdentifier(LowConfidenceTmdbClient()).identify(ParsedFileInfo("标题", 2024, "movie"))

    assert result.status == "need_confirm"
    assert result.tmdb_id == 1


def test_media_identifier_selects_highest_confidence_candidate():
    class MultiCandidateTmdbClient:
        def search_movie(self, title: str, year: int | None):
            return [
                TmdbCandidate(1, "movie", "低分", "Low", 2024, 0.5),
                TmdbCandidate(2, "movie", "高分", "High", 2024, 0.9),
            ]

        def search_tv(self, title: str, year: int | None):
            return []

        def get_details(self, tmdb_id: int, media_type: str):
            return None

    result = MediaIdentifier(MultiCandidateTmdbClient()).identify(ParsedFileInfo("标题", 2024, "movie"))

    assert result.status == "need_confirm"
    assert result.tmdb_id == 2
    assert result.title_cn == "高分"


def test_media_identifier_auto_searches_movie_and_tv():
    class AutoTmdbClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def search_movie(self, title: str, year: int | None):
            self.calls.append("movie")
            return [TmdbCandidate(1, "movie", "电影", "Movie", 2024, 0.8)]

        def search_tv(self, title: str, year: int | None):
            self.calls.append("tv")
            return [TmdbCandidate(2, "tv", "剧集", "TV", 2024, 0.9)]

        def get_details(self, tmdb_id: int, media_type: str):
            return None

    tmdb_client = AutoTmdbClient()
    result = MediaIdentifier(tmdb_client).identify(ParsedFileInfo("标题", 2024, "auto"))

    assert tmdb_client.calls == ["movie", "tv"]
    assert result.status == "need_confirm"
    assert result.tmdb_id == 2
    assert result.media_type == "tv"


def test_media_identifier_anime_searches_tv_only():
    class TvOnlyTmdbClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def search_movie(self, title: str, year: int | None):
            self.calls.append("movie")
            return [TmdbCandidate(1, "movie", "电影", "Movie", 2024, 0.95)]

        def search_tv(self, title: str, year: int | None):
            self.calls.append("tv")
            return [TmdbCandidate(2, "tv", "动画", "Anime", 2024, 0.95)]

        def get_details(self, tmdb_id: int, media_type: str):
            return None

    tmdb_client = TvOnlyTmdbClient()
    result = MediaIdentifier(tmdb_client).identify(ParsedFileInfo("动画", 2024, "anime"))

    assert tmdb_client.calls == ["tv"]
    assert result.status == "recognized"
    assert result.tmdb_id == 2
    assert result.media_type == "anime"


def test_media_identifier_variety_searches_tv_only():
    class TvOnlyTmdbClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def search_movie(self, title: str, year: int | None):
            self.calls.append("movie")
            return [TmdbCandidate(1, "movie", "电影", "Movie", 2024, 0.95)]

        def search_tv(self, title: str, year: int | None):
            self.calls.append("tv")
            return [TmdbCandidate(2, "tv", "综艺", "Variety", 2024, 0.95)]

        def get_details(self, tmdb_id: int, media_type: str):
            return None

    tmdb_client = TvOnlyTmdbClient()
    result = MediaIdentifier(tmdb_client).identify(ParsedFileInfo("综艺", 2024, "variety"))

    assert tmdb_client.calls == ["tv"]
    assert result.status == "recognized"
    assert result.tmdb_id == 2
    assert result.media_type == "variety"


def test_media_identifier_unknown_media_type_fallback():
    result = MediaIdentifier(FakeTmdbClient()).identify(ParsedFileInfo("标题", 2024, "documentary"))

    assert result.status == "unsupported_media_type"
    assert result.title_cn == "标题"
