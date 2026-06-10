from dataclasses import dataclass

from app.services.quality_scorer import MediaQuality, QualityDecision, QualityProfileInput, QualityScorer


@dataclass(slots=True)
class ConflictResult:
    conflict_status: str
    upgrade_suggestion: str
    decision: QualityDecision | None = None


class ConflictResolver:
    def resolve(
        self,
        target_exists: bool,
        new_quality: MediaQuality,
        old_quality: MediaQuality | None,
        profile: QualityProfileInput,
    ) -> ConflictResult:
        if not target_exists:
            return ConflictResult(conflict_status="none", upgrade_suggestion="none")

        if old_quality is None:
            return ConflictResult(conflict_status="path_exists", upgrade_suggestion="manual_confirm")

        decision = QualityScorer().compare(new_quality, old_quality, profile)
        return ConflictResult(
            conflict_status="same_media_exists",
            upgrade_suggestion=decision.suggestion,
            decision=decision,
        )
