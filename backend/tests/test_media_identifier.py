from app.clients.protocols import TmdbCandidate
from app.services.media_identifier import MediaIdentifier, ParsedFileInfo


class FakeTmdbClient:
    def search_movie(self, title: str, year: int | None):
        assert title == "流浪地球"
        assert year == 2019
        return [TmdbCandidate(tmdb_id=535167, media_type="movie", title_cn="流浪地球", title_original="The Wandering Earth", year=2019, confidence=0.95)]

    def search_tv(self, title: str, year: int | None):
        return []

    def get_details(self, tmdb_id: int, media_type: str):
        return None


def test_media_identifier_uses_tmdb_candidate():
    identifier = MediaIdentifier(tmdb_client=FakeTmdbClient())
    parsed = ParsedFileInfo(title="流浪地球", year=2019, media_type="movie", fields={"title": "流浪地球", "year": "2019"})

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
    parsed = ParsedFileInfo(title="未知电影", year=2024, media_type="movie", fields={"title": "未知电影"})

    result = identifier.identify(parsed)

    assert result.status == "tmdb_failed"
    assert result.title_cn == "未知电影"
