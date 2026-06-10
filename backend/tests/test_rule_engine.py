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


def test_rule_engine_prefers_lower_priority_rule_when_multiple_rules_match():
    engine = RuleEngine()
    high_priority_rule = RenameRuleInput(
        id=10,
        name="high-priority",
        media_type="movie",
        pattern=r"(?P<title>.+)",
        template="{title}",
        priority=20,
        enabled=True,
    )
    low_priority_rule = RenameRuleInput(
        id=9,
        name="low-priority",
        media_type="movie",
        pattern=r"(?P<title>.+)",
        template="{title}",
        priority=1,
        enabled=True,
    )

    result = engine.match(
        "流浪地球 2019 2160p WEB-DL.mkv",
        [high_priority_rule, low_priority_rule],
        media_type="movie",
    )

    assert result.matched is True
    assert result.rule_id == 9


def test_rule_engine_skips_disabled_rules_even_when_they_match_first():
    engine = RuleEngine()
    disabled_rule = RenameRuleInput(
        id=11,
        name="disabled",
        media_type="movie",
        pattern=r"(?P<title>.+)",
        template="{title}",
        priority=1,
        enabled=False,
    )
    enabled_rule = RenameRuleInput(
        id=12,
        name="enabled",
        media_type="movie",
        pattern=r"(?P<title>.+)",
        template="{title}",
        priority=10,
        enabled=True,
    )

    result = engine.match(
        "流浪地球 2019 2160p WEB-DL.mkv",
        [disabled_rule, enabled_rule],
        media_type="movie",
    )

    assert result.matched is True
    assert result.rule_id == 12


def test_rule_engine_matches_general_and_current_media_type_rules():
    engine = RuleEngine()
    general_rule = RenameRuleInput(
        id=13,
        name="general",
        media_type="general",
        pattern=r"(?P<title>.+)",
        template="{title}",
        priority=1,
        enabled=True,
    )
    current_type_rule = RenameRuleInput(
        id=14,
        name="current-type",
        media_type="movie",
        pattern=r"(?P<title>.+)",
        template="{title}",
        priority=1,
        enabled=True,
    )

    general_result = engine.match("流浪地球.mkv", [general_rule], media_type="movie")
    current_type_result = engine.match("流浪地球.mkv", [current_type_rule], media_type="movie")

    assert general_result.matched is True
    assert general_result.rule_id == 13
    assert current_type_result.matched is True
    assert current_type_result.rule_id == 14


def test_rule_engine_skips_other_media_type_rules():
    engine = RuleEngine()
    other_type_rule = RenameRuleInput(
        id=15,
        name="episode",
        media_type="episode",
        pattern=r"(?P<title>.+)",
        template="{title}",
        priority=1,
        enabled=True,
    )
    movie_rule = RenameRuleInput(
        id=16,
        name="movie",
        media_type="movie",
        pattern=r"(?P<title>.+)",
        template="{title}",
        priority=10,
        enabled=True,
    )

    result = engine.match("流浪地球.mkv", [other_type_rule, movie_rule], media_type="movie")

    assert result.matched is True
    assert result.rule_id == 16


def test_rule_engine_returns_no_match_error_when_no_rule_matches():
    engine = RuleEngine()
    rule = RenameRuleInput(
        id=17,
        name="year-only",
        media_type="movie",
        pattern=r"(?P<year>20\d{2})",
        template="{year}",
        priority=1,
        enabled=True,
    )

    result = engine.match("没有年份.mkv", [rule], media_type="movie")

    assert result.matched is False
    assert result.error == "没有命中规则"


def test_rule_engine_strips_captured_field_values():
    engine = RuleEngine()
    rule = RenameRuleInput(
        id=18,
        name="title-with-spaces",
        media_type="movie",
        pattern=r"(?P<title>.+?)20\d{2}",
        template="{title}",
        priority=1,
        enabled=True,
    )

    result = engine.match(" 流浪地球  2019.mkv", [rule], media_type="movie")

    assert result.matched is True
    assert result.fields["title"] == "流浪地球"


def test_rule_engine_omits_unmatched_optional_named_groups():
    engine = RuleEngine()
    rule = RenameRuleInput(
        id=3,
        name="optional-season",
        media_type="movie",
        pattern=r"(?P<title>.+?)(?: S(?P<season>\d+))?",
        template="{title}",
        priority=1,
        enabled=True,
    )

    result = engine.match("电影名.mkv", [rule], media_type="movie")

    assert result.matched is True
    assert "season" not in result.fields


def test_rule_engine_keeps_explicitly_captured_extension():
    engine = RuleEngine()
    rule = RenameRuleInput(
        id=4,
        name="explicit-ext",
        media_type="movie",
        pattern=r"(?P<title>.+)\.(?P<ext>custom)",
        template="{title}.{ext}",
        priority=1,
        enabled=True,
    )

    result = engine.match("电影名.custom.mkv", [rule], media_type="movie")

    assert result.matched is True
    assert result.fields["ext"] == "custom"


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
