from dataclasses import dataclass, field

from app.clients.protocols import Pan115ClientProtocol, RemoteFile
from app.services.media_identifier import MediaIdentifier, MediaIdentifyResult, ParsedFileInfo
from app.services.rule_engine import RenameRuleInput, RuleEngine
from app.services.template_engine import TemplateEngine


VIDEO_EXTENSIONS = {"mkv", "mp4", "avi", "mov", "ts", "m2ts", "wmv"}


@dataclass(frozen=True)
class PreviewBuildItem:
    file_id: str
    original_path: str
    new_path: str
    file_size: int
    media_type: str
    title: str
    year: int | None
    season: int | None
    episode: int | None
    tmdb_id: int | None
    tmdb_title: str
    confidence: float
    matched_rule_id: int | None
    quality_score: float
    conflict_status: str
    upgrade_suggestion: str
    final_action: str
    status: str
    error_message: str = ""


@dataclass(frozen=True)
class PreviewBuildResult:
    file_count: int
    recognized_count: int
    need_confirm_count: int
    items: list[PreviewBuildItem] = field(default_factory=list)


class PreviewBuilder:
    def __init__(
        self,
        pan_client: Pan115ClientProtocol,
        identifier: MediaIdentifier,
        rule_engine: RuleEngine | None = None,
        template_engine: TemplateEngine | None = None,
    ) -> None:
        self.pan_client = pan_client
        self.identifier = identifier
        self.rule_engine = rule_engine or RuleEngine()
        self.template_engine = template_engine or TemplateEngine()

    def build(
        self,
        source_dir_id: str,
        target_dir: str,
        media_type: str,
        recursive: bool,
        rules: list[RenameRuleInput],
    ) -> PreviewBuildResult:
        files = self._collect_files(source_dir_id, recursive)
        items: list[PreviewBuildItem] = []
        recognized_count = 0
        need_confirm_count = 0

        for file in files:
            rule_match = self.rule_engine.match(file.name, rules, media_type)
            if not rule_match.matched:
                need_confirm_count += 1
                items.append(self._error_item(file, media_type, rule_match.error or "no matched rule"))
                continue

            parsed = ParsedFileInfo(
                title=rule_match.fields.get("title", ""),
                year=self._int_or_none(rule_match.fields.get("year")),
                media_type=media_type if media_type != "auto" else "movie",
                fields=rule_match.fields,
            )
            identified = self.identifier.identify(parsed)
            if identified.status == "recognized":
                recognized_count += 1
            else:
                need_confirm_count += 1

            fields = {
                **rule_match.fields,
                "title_cn": identified.title_cn,
                "title_original": identified.title_original,
                "year": identified.year or parsed.year or "",
            }
            fields.update(self._moviepilot_fields(file, fields))
            render = self.template_engine.render(rule_match.template, fields)
            if not render.ok:
                need_confirm_count += 1
                error_message = render.error
                if render.missing_fields:
                    error_message = f"missing fields: {', '.join(render.missing_fields)}"
                items.append(self._error_item(file, identified.media_type, error_message))
                continue

            final_path = self._with_target_dir(render.path, target_dir)
            items.append(
                PreviewBuildItem(
                    file_id=file.file_id,
                    original_path=file.path,
                    new_path=final_path,
                    file_size=file.size,
                    media_type=identified.media_type,
                    title=identified.title_cn,
                    year=identified.year or parsed.year,
                    season=self._int_or_none(rule_match.fields.get("season")),
                    episode=self._int_or_none(rule_match.fields.get("episode")),
                    tmdb_id=identified.tmdb_id,
                    tmdb_title=identified.title_cn,
                    confidence=identified.confidence,
                    matched_rule_id=rule_match.rule_id,
                    quality_score=0,
                    conflict_status="none",
                    upgrade_suggestion="none",
                    final_action="rename_move" if final_path != file.path else "skip",
                    status=identified.status,
                )
            )

        return PreviewBuildResult(
            file_count=len(files),
            recognized_count=recognized_count,
            need_confirm_count=need_confirm_count,
            items=items,
        )

    def _collect_files(self, source_dir_id: str, recursive: bool) -> list[RemoteFile]:
        if recursive and hasattr(self.pan_client, "list_dir_recursive"):
            items = self.pan_client.list_dir_recursive(source_dir_id)
        else:
            items = self.pan_client.list_dir(source_dir_id)

        return [
            item
            for item in items
            if not item.is_dir and self._is_video_file(item.name)
        ]

    def _with_target_dir(self, path: str, target_dir: str) -> str:
        if path.startswith("/"):
            return path
        return f"{target_dir.rstrip('/')}/{path.lstrip('/')}"

    def _is_video_file(self, filename: str) -> bool:
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return extension in VIDEO_EXTENSIONS

    def _moviepilot_fields(self, file: RemoteFile, fields: dict[str, object]) -> dict[str, object]:
        extension = file.name.rsplit(".", 1)[-1] if "." in file.name else ""
        season = self._int_or_none(fields.get("season"))
        episode = self._int_or_none(fields.get("episode"))
        return {
            "title": fields.get("title_cn") or fields.get("title") or "",
            "originalTitle": fields.get("title_original") or fields.get("title") or "",
            "fileExt": f".{extension}" if extension else "",
            "videoFormat": fields.get("videoFormat") or fields.get("resolution") or "",
            "season": f"{season:02d}" if season is not None else fields.get("season", ""),
            "episode": f"{episode:02d}" if episode is not None else fields.get("episode", ""),
            "season_episode": self._season_episode(season, episode),
            "part": fields.get("part", ""),
        }

    def _season_episode(self, season: int | None, episode: int | None) -> str:
        if season is None or episode is None:
            return ""
        return f"S{season:02d}E{episode:02d}"

    def _error_item(self, file: RemoteFile, media_type: str, error_message: str) -> PreviewBuildItem:
        return PreviewBuildItem(
            file_id=file.file_id,
            original_path=file.path,
            new_path=file.path,
            file_size=file.size,
            media_type=media_type,
            title="",
            year=None,
            season=None,
            episode=None,
            tmdb_id=None,
            tmdb_title="",
            confidence=0,
            matched_rule_id=None,
            quality_score=0,
            conflict_status="none",
            upgrade_suggestion="none",
            final_action="skip",
            status="error",
            error_message=error_message,
        )

    def _int_or_none(self, value: object) -> int | None:
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
