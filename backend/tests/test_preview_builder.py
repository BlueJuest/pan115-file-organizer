from app.clients.mock_pan115 import MockPan115Client
from app.clients.protocols import RemoteFile
from app.services.media_identifier import MediaIdentifyResult
from app.services.preview_builder import PreviewBuilder
from app.services.rule_engine import RenameRuleInput


class FakeIdentifier:
    def identify(self, parsed):
        assert parsed.title == "流浪地球"
        assert parsed.year == 2019
        assert parsed.media_type == "movie"
        return MediaIdentifyResult(
            status="recognized",
            media_type="movie",
            title_cn="流浪地球",
            title_original="The Wandering Earth",
            year=2019,
            tmdb_id=535167,
            confidence=0.95,
        )


def test_preview_builder_builds_rename_move_item_for_recognized_movie():
    pan_client = MockPan115Client(
        [
            RemoteFile(
                file_id="src",
                name="待整理",
                path="/待整理",
                parent_id="0",
                is_dir=True,
            ),
            RemoteFile(
                file_id="f1",
                name="流浪地球 2019 2160p.mkv",
                path="/待整理/流浪地球 2019 2160p.mkv",
                parent_id="src",
                is_dir=False,
                size=1024,
            ),
        ]
    )
    rules = [
        RenameRuleInput(
            id=1,
            name="电影规则",
            media_type="movie",
            pattern=r"^(?P<title>.+?)\s+(?P<year>\d{4})\s+(?P<quality>\d+p)\.(?P<ext>mkv)$",
            template="/电影/{title_cn} ({year})/{title_cn} ({year}) - {quality}.{ext}",
            priority=1,
            enabled=True,
        )
    ]
    builder = PreviewBuilder(pan_client=pan_client, identifier=FakeIdentifier())

    result = builder.build(
        source_dir_id="src",
        target_dir="/电影",
        media_type="movie",
        recursive=False,
        rules=rules,
    )

    assert result.file_count == 1
    assert result.recognized_count == 1
    assert result.need_confirm_count == 0
    item = result.items[0]
    assert item.file_id == "f1"
    assert item.new_path == "/电影/流浪地球 (2019)/流浪地球 (2019) - 2160p.mkv"
    assert item.final_action == "rename_move"
