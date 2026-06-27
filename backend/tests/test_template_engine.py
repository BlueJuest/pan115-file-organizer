from app.services.template_engine import TemplateEngine


def test_template_engine_renders_moviepilot_jinja_template():
    engine = TemplateEngine()

    result = engine.render(
        "{{title}}{% if year %} ({{year}}){% endif %}/{{title}}{% if part %}-{{part}}{% endif %}{% if videoFormat %} - {{videoFormat}}{% endif %}{{fileExt}}",
        {"title": "Avatar", "year": 2009, "part": "CD1", "videoFormat": "BluRay-1080p", "fileExt": ".mkv"},
    )

    assert result.ok is True
    assert result.path == "Avatar (2009)/Avatar-CD1 - BluRay-1080p.mkv"


def test_template_engine_renders_moviepilot_tv_template():
    engine = TemplateEngine()

    result = engine.render(
        "{{title}}{% if year %} ({{year}}){% endif %}/Season {{season}}/{{title}} - {{season_episode}}{% if episode %} - Episode {{episode}}{% endif %}{{fileExt}}",
        {"title": "Show", "year": 2024, "season": "01", "season_episode": "S01E02", "episode": "02", "fileExt": ".mkv"},
    )

    assert result.ok is True
    assert result.path == "Show (2024)/Season 01/Show - S01E02 - Episode 02.mkv"


def test_template_engine_renders_and_cleans_path_parts():
    engine = TemplateEngine()

    result = engine.render(
        "/电影/{title_cn} ({year})/{title_cn}:{year}.{ext}",
        {"title_cn": "电影/名", "year": 2024, "ext": "mkv"},
    )

    assert result.ok is True
    assert result.path == "/电影/电影_名 (2024)/电影_名_2024.mkv"


def test_template_engine_renders_format_specs():
    engine = TemplateEngine()

    result = engine.render(
        "/剧集/S{season:02d}E{episode:02d}.mkv",
        {"season": 1, "episode": 2},
    )

    assert result.ok is True
    assert result.path == "/剧集/S01E02.mkv"


def test_template_engine_renders_single_field_with_literal_suffix():
    engine = TemplateEngine()

    result = engine.render("/{title}.mkv", {"title": "测试"})

    assert result.ok is True
    assert result.path == "/测试.mkv"


def test_template_engine_renders_static_template():
    engine = TemplateEngine()

    result = engine.render("/固定目录/文件.mkv", {})

    assert result.ok is True
    assert result.path == "/固定目录/文件.mkv"


def test_template_engine_reports_missing_field():
    engine = TemplateEngine()

    result = engine.render("/电影/{title_cn} ({year}).{ext}", {"title_cn": "测试", "ext": "mkv"})

    assert result.ok is False
    assert result.missing_fields == ["year"]


def test_template_engine_reports_template_syntax_error():
    engine = TemplateEngine()

    result = engine.render("/电影/{title", {"title": "测试"})

    assert result.ok is False
    assert result.error


def test_template_engine_reports_jinja_syntax_error():
    engine = TemplateEngine()

    result = engine.render("{{ title ", {"title": "Avatar"})

    assert result.ok is False
    assert result.error


def test_template_engine_reports_unsupported_attribute_access_error():
    engine = TemplateEngine()

    result = engine.render("/{title.missing}", {"title": "测试"})

    assert result.ok is False
    assert result.error
