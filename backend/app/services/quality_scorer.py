from dataclasses import dataclass, field


@dataclass(slots=True)
class MediaQuality:
    resolution: str = ""
    source: str = ""
    video_codec: str = ""
    audio_codec: str = ""
    size: int = 0
    has_subtitle: bool = False


@dataclass(slots=True)
class QualityProfileInput:
    resolution_weight: int
    source_weight: int
    video_codec_weight: int
    audio_codec_weight: int
    size_weight: int
    subtitle_weight: int
    min_upgrade_delta: int
    default_old_file_action: str
    resolution_order: list[str] = field(default_factory=list)
    source_order: list[str] = field(default_factory=list)
    video_codec_order: list[str] = field(default_factory=list)
    audio_codec_order: list[str] = field(default_factory=list)

    @classmethod
    def default(cls) -> "QualityProfileInput":
        return cls(
            resolution_weight=40,
            source_weight=25,
            video_codec_weight=15,
            audio_codec_weight=10,
            size_weight=5,
            subtitle_weight=5,
            min_upgrade_delta=15,
            default_old_file_action="move_to_recycle",
            resolution_order=["2160p", "1080p", "720p", "480p"],
            source_order=["BluRay", "WEB-DL", "WEBRip", "HDTV"],
            video_codec_order=["H.265", "HEVC", "H.264", "AVC"],
            audio_codec_order=["TrueHD", "DTS-HD", "DDP", "DD", "AAC"],
        )


@dataclass(slots=True)
class QualityDecision:
    new_score: float
    old_score: float
    delta: float
    suggestion: str
    old_file_action: str


class QualityScorer:
    def score(self, quality: MediaQuality, profile: QualityProfileInput) -> float:
        score = 0.0
        score += self._rank_score(quality.resolution, profile.resolution_order, profile.resolution_weight)
        score += self._rank_score(quality.source, profile.source_order, profile.source_weight)
        score += self._rank_score(quality.video_codec, profile.video_codec_order, profile.video_codec_weight)
        score += self._rank_score(quality.audio_codec, profile.audio_codec_order, profile.audio_codec_weight)
        score += self._size_score(quality.size, profile.size_weight)
        if quality.has_subtitle:
            score += profile.subtitle_weight
        return round(score, 2)

    def compare(
        self,
        new_quality: MediaQuality,
        old_quality: MediaQuality,
        profile: QualityProfileInput,
    ) -> QualityDecision:
        new_score = self.score(new_quality, profile)
        old_score = self.score(old_quality, profile)
        delta = round(new_score - old_score, 2)
        suggestion = "replace_old" if delta >= profile.min_upgrade_delta else "keep_both"
        return QualityDecision(
            new_score=new_score,
            old_score=old_score,
            delta=delta,
            suggestion=suggestion,
            old_file_action=profile.default_old_file_action,
        )

    def _rank_score(self, value: str, order: list[str], weight: int) -> float:
        normalized_value = value.lower()
        normalized_order = [item.lower() for item in order]
        if normalized_value not in normalized_order:
            return 0.0

        index = normalized_order.index(normalized_value)
        return weight * (len(order) - index) / len(order)

    def _size_score(self, size: int, weight: int) -> float:
        if size <= 0:
            return 0.0
        return weight * min(size, 20_000) / 20_000
