from app.services.template_engine import TemplateEngine


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


def test_template_engine_reports_unsupported_attribute_access_error():
    engine = TemplateEngine()

    result = engine.render("/{title.missing}", {"title": "测试"})

    assert result.ok is False
    assert result.error
