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


class NeedConfirmIdentifier:
    def identify(self, parsed):
        return MediaIdentifyResult(
            status="need_confirm",
            media_type="movie",
            title_cn=parsed.title,
            title_original="",
            year=parsed.year,
            tmdb_id=None,
            confidence=0.4,
        )


class UnexpectedIdentifier:
    def identify(self, parsed):
        raise AssertionError("identifier should not be called")


def movie_rule() -> RenameRuleInput:
    return RenameRuleInput(
        id=1,
        name="电影规则",
        media_type="movie",
        pattern=r"(?P<title>.+?) (?P<year>20\d{2}) (?P<resolution>\d{3,4}p)",
        template="/电影/{title_cn} ({year})/{title_cn} ({year}) - {resolution}.{ext}",
        priority=1,
        enabled=True,
    )


def test_preview_builder_builds_rename_move_item_for_recognized_movie():
    pan_client = MockPan115Client(
        [
            RemoteFile("root", "root", "/", "", True),
            RemoteFile("src", "下载", "/下载", "root", True),
            RemoteFile(
                "f1",
                "流浪地球 2019 2160p.mkv",
                "/下载/流浪地球 2019 2160p.mkv",
                "src",
                False,
                12000,
            ),
        ]
    )
    builder = PreviewBuilder(pan_client=pan_client, identifier=FakeIdentifier())

    result = builder.build(
        source_dir_id="src",
        target_dir="/电影",
        media_type="movie",
        recursive=False,
        rules=[movie_rule()],
    )

    assert result.file_count == 1
    assert result.recognized_count == 1
    assert result.need_confirm_count == 0
    item = result.items[0]
    assert item.file_id == "f1"
    assert item.new_path == "/电影/流浪地球 (2019)/流浪地球 (2019) - 2160p.mkv"
    assert item.final_action == "rename_move"


def test_preview_builder_ignores_non_video_files():
    pan_client = MockPan115Client(
        [
            RemoteFile("root", "root", "/", "", True),
            RemoteFile("src", "下载", "/下载", "root", True),
            RemoteFile("note", "说明.txt", "/下载/说明.txt", "src", False, 10),
        ]
    )
    builder = PreviewBuilder(pan_client=pan_client, identifier=UnexpectedIdentifier())

    result = builder.build(
        source_dir_id="src",
        target_dir="/电影",
        media_type="movie",
        recursive=False,
        rules=[movie_rule()],
    )

    assert result.file_count == 0
    assert result.items == []


def test_preview_builder_returns_error_item_when_no_rule_matches():
    pan_client = MockPan115Client(
        [
            RemoteFile("root", "root", "/", "", True),
            RemoteFile("src", "下载", "/下载", "root", True),
            RemoteFile("f1", "未命名.mkv", "/下载/未命名.mkv", "src", False, 12000),
        ]
    )
    builder = PreviewBuilder(pan_client=pan_client, identifier=UnexpectedIdentifier())

    result = builder.build(
        source_dir_id="src",
        target_dir="/电影",
        media_type="movie",
        recursive=False,
        rules=[movie_rule()],
    )

    assert result.file_count == 1
    assert result.recognized_count == 0
    assert result.need_confirm_count == 1
    item = result.items[0]
    assert item.status == "error"
    assert item.final_action == "skip"
    assert item.original_path == "/下载/未命名.mkv"
    assert item.new_path == item.original_path


def test_preview_builder_counts_need_confirm_identifier_result():
    pan_client = MockPan115Client(
        [
            RemoteFile("root", "root", "/", "", True),
            RemoteFile("src", "下载", "/下载", "root", True),
            RemoteFile(
                "f1",
                "流浪地球 2019 2160p.mkv",
                "/下载/流浪地球 2019 2160p.mkv",
                "src",
                False,
                12000,
            ),
        ]
    )
    builder = PreviewBuilder(pan_client=pan_client, identifier=NeedConfirmIdentifier())

    result = builder.build(
        source_dir_id="src",
        target_dir="/电影",
        media_type="movie",
        recursive=False,
        rules=[movie_rule()],
    )

    assert result.file_count == 1
    assert result.recognized_count == 0
    assert result.need_confirm_count == 1
    assert result.items[0].status == "need_confirm"


def test_preview_builder_does_not_enter_subdirectories_when_not_recursive():
    pan_client = MockPan115Client(
        [
            RemoteFile("root", "root", "/", "", True),
            RemoteFile("src", "下载", "/下载", "root", True),
            RemoteFile("sub", "子目录", "/下载/子目录", "src", True),
            RemoteFile(
                "f1",
                "流浪地球 2019 2160p.mkv",
                "/下载/子目录/流浪地球 2019 2160p.mkv",
                "sub",
                False,
                12000,
            ),
        ]
    )
    builder = PreviewBuilder(pan_client=pan_client, identifier=UnexpectedIdentifier())

    result = builder.build(
        source_dir_id="src",
        target_dir="/电影",
        media_type="movie",
        recursive=False,
        rules=[movie_rule()],
    )

    assert result.file_count == 0
    assert result.items == []