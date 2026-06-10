from dataclasses import dataclass, field

from app.clients.protocols import TmdbCandidate, TmdbClientProtocol


@dataclass(slots=True)
class ParsedFileInfo:
    title: str
    year: int | None
    media_type: str
    fields: dict = field(default_factory=dict)


@dataclass(slots=True)
class MediaIdentifyResult:
    status: str
    media_type: str
    title_cn: str
    title_original: str = ""
    year: int | None = None
    tmdb_id: int | None = None
    confidence: float = 0
    candidates: list[TmdbCandidate] = field(default_factory=list)
    error: str = ""


class MediaIdentifier:
    def __init__(self, tmdb_client: TmdbClientProtocol | None = None) -> None:
        self.tmdb_client = tmdb_client

    def identify(self, parsed: ParsedFileInfo) -> MediaIdentifyResult:
        if self.tmdb_client is None:
            return self._fallback(parsed, "no_tmdb_client")
        if parsed.media_type not in {"movie", "tv", "anime", "variety", "auto"}:
            return self._fallback(parsed, "unsupported_media_type")

        try:
            candidates = self._search_candidates(parsed)
        except Exception as exc:
            return self._fallback(parsed, "tmdb_failed", str(exc))

        if not candidates:
            return self._fallback(parsed, "not_recognized")

        best = max(candidates, key=lambda candidate: candidate.confidence)
        status = "recognized" if len(candidates) == 1 and best.confidence >= 0.75 else "need_confirm"
        return MediaIdentifyResult(
            status=status,
            media_type=best.media_type,
            title_cn=best.title_cn,
            title_original=best.title_original,
            year=best.year,
            tmdb_id=best.tmdb_id,
            confidence=best.confidence,
            candidates=candidates,
        )

    def _search_candidates(self, parsed: ParsedFileInfo) -> list[TmdbCandidate]:
        if self.tmdb_client is None:
            return []
        if parsed.media_type == "movie":
            return self.tmdb_client.search_movie(parsed.title, parsed.year)
        if parsed.media_type in {"tv", "anime", "variety"}:
            return self.tmdb_client.search_tv(parsed.title, parsed.year)
        if parsed.media_type == "auto":
            return [
                *self.tmdb_client.search_movie(parsed.title, parsed.year),
                *self.tmdb_client.search_tv(parsed.title, parsed.year),
            ]
        raise ValueError(f"不支持的媒体类型: {parsed.media_type}")

    def _fallback(
        self,
        parsed: ParsedFileInfo,
        status: str,
        error: str = "",
    ) -> MediaIdentifyResult:
        return MediaIdentifyResult(
            status=status,
            media_type=parsed.media_type,
            title_cn=parsed.title,
            year=parsed.year,
            error=error,
        )
