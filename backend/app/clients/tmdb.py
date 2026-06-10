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
        return [self._to_candidate(item, "movie") for item in response.json().get("results", [])]

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
        return [self._to_candidate(item, "tv") for item in response.json().get("results", [])]

    def get_details(self, tmdb_id: int, media_type: str) -> TmdbCandidate | None:
        normalized_type = "movie" if media_type == "movie" else "tv"
        response = self.client.get(
            f"/{normalized_type}/{tmdb_id}",
            params={"api_key": self.api_key, "language": self.language},
        )
        response.raise_for_status()
        return self._to_candidate(response.json(), normalized_type)

    def _to_candidate(self, item: dict, media_type: str) -> TmdbCandidate:
        title_cn = item.get("title") or item.get("name") or ""
        title_original = item.get("original_title") or item.get("original_name") or title_cn
        date_value = item.get("release_date") or item.get("first_air_date") or ""
        return TmdbCandidate(
            tmdb_id=int(item.get("id") or 0),
            media_type=media_type,
            title_cn=title_cn,
            title_original=title_original,
            year=self._parse_year(date_value),
            confidence=float(item.get("vote_average") or 0) / 10,
            overview=item.get("overview") or "",
            poster_path=item.get("poster_path") or "",
        )

    def _parse_year(self, date_value: str) -> int | None:
        if len(date_value) < 4:
            return None
        try:
            return int(date_value[:4])
        except ValueError:
            return None
