import httpx

from app.clients.protocols import TmdbCandidate


class TmdbClient:
    def __init__(self, api_key: str, language: str = "zh-CN") -> None:
        self.api_key = api_key
        self.language = language
        self.client = httpx.Client(timeout=10, base_url="https://api.themoviedb.org/3")

    def search_movie(self, title: str, year: int | None) -> list[TmdbCandidate]:
        params: dict[str, str | int] = {
            "api_key": self.api_key,
            "query": title,
            "language": self.language,
        }
        if year is not None:
            params["year"] = year
        response = self.client.get("/search/movie", params=params)
        response.raise_for_status()
        return [
            self._to_candidate(item, "movie", title, year, index)
            for index, item in enumerate(response.json().get("results", []))
        ]

    def search_tv(self, title: str, year: int | None) -> list[TmdbCandidate]:
        params: dict[str, str | int] = {
            "api_key": self.api_key,
            "query": title,
            "language": self.language,
        }
        if year is not None:
            params["first_air_date_year"] = year
        response = self.client.get("/search/tv", params=params)
        response.raise_for_status()
        return [
            self._to_candidate(item, "tv", title, year, index)
            for index, item in enumerate(response.json().get("results", []))
        ]

    def get_details(self, tmdb_id: int, media_type: str) -> TmdbCandidate | None:
        normalized_type = self._normalize_media_type(media_type)
        response = self.client.get(
            f"/{normalized_type}/{tmdb_id}",
            params={"api_key": self.api_key, "language": self.language},
        )
        response.raise_for_status()
        item = response.json()
        if not item.get("overview") and self.language != "en-US":
            fallback_response = self.client.get(
                f"/{normalized_type}/{tmdb_id}",
                params={"api_key": self.api_key, "language": "en-US"},
            )
            fallback_response.raise_for_status()
            fallback_item = fallback_response.json()
            item["overview"] = fallback_item.get("overview") or ""
        return self._to_candidate(item, normalized_type, "", None, 0, confidence=1.0)

    def _normalize_media_type(self, media_type: str) -> str:
        if media_type == "movie":
            return "movie"
        if media_type in {"tv", "anime", "variety"}:
            return "tv"
        raise ValueError(f"不支持的媒体类型: {media_type}")

    def _to_candidate(
        self,
        item: dict,
        media_type: str,
        query_title: str,
        query_year: int | None,
        index: int,
        confidence: float | None = None,
    ) -> TmdbCandidate:
        title_cn = item.get("title") or item.get("name") or ""
        title_original = item.get("original_title") or item.get("original_name") or title_cn
        date_value = item.get("release_date") or item.get("first_air_date") or ""
        candidate_year = self._parse_year(date_value)
        return TmdbCandidate(
            tmdb_id=int(item.get("id") or 0),
            media_type=media_type,
            title_cn=title_cn,
            title_original=title_original,
            year=candidate_year,
            confidence=(
                confidence
                if confidence is not None
                else self._calculate_confidence(query_title, title_cn, title_original, query_year, candidate_year, index)
            ),
            overview=item.get("overview") or "",
            poster_path=item.get("poster_path") or "",
            backdrop_path=item.get("backdrop_path") or "",
            vote_average=item.get("vote_average"),
            genres=[str(genre.get("name")) for genre in item.get("genres", []) if genre.get("name")],
        )

    def _calculate_confidence(
        self,
        query_title: str,
        title_cn: str,
        title_original: str,
        query_year: int | None,
        candidate_year: int | None,
        index: int,
    ) -> float:
        query = self._normalize_title(query_title)
        titles = [self._normalize_title(title_cn), self._normalize_title(title_original)]
        score = 0.25
        if query and query in titles:
            score = 0.75
        elif query and any(query in title or title in query for title in titles if title):
            score = 0.6

        if query_year is not None and candidate_year is not None:
            score += 0.15 if query_year == candidate_year else -0.2
        elif query_year is not None:
            score -= 0.05

        score += max(0.0, 0.1 - min(index, 10) * 0.01)
        return round(min(1.0, max(0.0, score)), 4)

    def _normalize_title(self, title: str) -> str:
        return "".join(title.lower().split())

    def _parse_year(self, date_value: str) -> int | None:
        if len(date_value) < 4:
            return None
        try:
            return int(date_value[:4])
        except ValueError:
            return None
