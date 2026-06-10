from app.services.quality_scorer import MediaQuality, QualityProfileInput, QualityScorer
from app.services.conflict_resolver import ConflictResolver


def test_quality_scorer_prefers_2160p_h265_over_1080p_h264():
    scorer = QualityScorer()
    profile = QualityProfileInput.default()

    old = MediaQuality(resolution="1080p", source="WEB-DL", video_codec="H.264", audio_codec="AAC", size=5_000, has_subtitle=False)
    new = MediaQuality(resolution="2160p", source="WEB-DL", video_codec="H.265", audio_codec="DDP", size=15_000, has_subtitle=True)

    decision = scorer.compare(new, old, profile)

    assert decision.new_score > decision.old_score
    assert decision.suggestion == "replace_old"
    assert decision.old_file_action == "move_to_recycle"


def test_quality_scorer_keeps_old_when_delta_is_too_small():
    scorer = QualityScorer()
    profile = QualityProfileInput.default()

    old = MediaQuality(resolution="1080p", source="WEB-DL", video_codec="H.264", audio_codec="AAC", size=5_000, has_subtitle=True)
    new = MediaQuality(resolution="1080p", source="WEB-DL", video_codec="H.264", audio_codec="AAC", size=5_100, has_subtitle=True)

    decision = scorer.compare(new, old, profile)

    assert decision.suggestion == "keep_both"


def test_quality_scorer_scores_case_insensitive_values_and_caps_size():
    scorer = QualityScorer()
    profile = QualityProfileInput.default()

    quality = MediaQuality(resolution="2160P", source="bluray", video_codec="h.265", audio_codec="truehd", size=25_000, has_subtitle=True)

    assert scorer.score(quality, profile) == 100


def test_quality_scorer_scores_unknown_values_as_zero_and_size_proportionally():
    scorer = QualityScorer()
    profile = QualityProfileInput.default()

    quality = MediaQuality(resolution="unknown", source="unknown", video_codec="unknown", audio_codec="unknown", size=10_000, has_subtitle=True)

    assert scorer.score(quality, profile) == 7.5


def test_conflict_resolver_returns_none_when_target_does_not_exist():
    resolver = ConflictResolver()
    profile = QualityProfileInput.default()
    new = MediaQuality(resolution="2160p", source="WEB-DL", video_codec="H.265", audio_codec="DDP", size=15_000, has_subtitle=True)

    result = resolver.resolve(target_exists=False, new_quality=new, old_quality=None, profile=profile)

    assert result.conflict_status == "none"
    assert result.upgrade_suggestion == "none"
    assert result.decision is None


def test_conflict_resolver_requires_manual_confirmation_when_path_exists_without_quality():
    resolver = ConflictResolver()
    profile = QualityProfileInput.default()
    new = MediaQuality(resolution="2160p", source="WEB-DL", video_codec="H.265", audio_codec="DDP", size=15_000, has_subtitle=True)

    result = resolver.resolve(target_exists=True, new_quality=new, old_quality=None, profile=profile)

    assert result.conflict_status == "path_exists"
    assert result.upgrade_suggestion == "manual_confirm"
    assert result.decision is None


def test_conflict_resolver_suggests_quality_decision_when_same_media_exists():
    resolver = ConflictResolver()
    profile = QualityProfileInput.default()

    old = MediaQuality(resolution="1080p", source="WEB-DL", video_codec="H.264", audio_codec="AAC", size=5_000, has_subtitle=False)
    new = MediaQuality(resolution="2160p", source="WEB-DL", video_codec="H.265", audio_codec="DDP", size=15_000, has_subtitle=True)

    result = resolver.resolve(target_exists=True, new_quality=new, old_quality=old, profile=profile)

    assert result.conflict_status == "same_media_exists"
    assert result.upgrade_suggestion == "replace_old"
    assert result.decision is not None
    assert result.decision.old_file_action == "move_to_recycle"
