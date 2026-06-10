from app.services.rule_engine import RenameRuleInput, RuleEngine


def test_rule_engine_extracts_named_groups_and_extension():
    engine = RuleEngine()
    rule = RenameRuleInput(
        id=1,
        name="movie-year",
        media_type="movie",
        pattern=r"(?P<title>.+?)[ ._-]+(?P<year>20\d{2})[ ._-]+(?P<resolution>2160p|1080p)",
        template="/电影/{title} ({year})/{title} ({year}) - {resolution}.{ext}",
        priority=10,
        enabled=True,
    )

    result = engine.match("流浪地球 2019 2160p WEB-DL.mkv", [rule], media_type="movie")

    assert result.matched is True
    assert result.rule_id == 1
    assert result.fields["title"] == "流浪地球"
    assert result.fields["year"] == "2019"
    assert result.fields["resolution"] == "2160p"
    assert result.fields["ext"] == "mkv"


def test_rule_engine_returns_error_for_invalid_regex():
    engine = RuleEngine()
    rule = RenameRuleInput(
        id=2,
        name="bad",
        media_type="general",
        pattern="(?P<title>",
        template="{title}",
        priority=1,
        enabled=True,
    )

    result = engine.match("anything.mkv", [rule], media_type="movie")

    assert result.matched is False
    assert "missing" in result.error.lower() or "unterminated" in result.error.lower()
