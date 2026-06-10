from app.services.template_engine import TemplateEngine


def test_template_engine_renders_and_cleans_path_parts():
    engine = TemplateEngine()

    result = engine.render(
        "/电影/{title_cn} ({year})/{title_cn}:{year}.{ext}",
        {"title_cn": "电影/名", "year": 2024, "ext": "mkv"},
    )

    assert result.ok is True
    assert result.path == "/电影/电影_名 (2024)/电影_名_2024.mkv"


def test_template_engine_reports_missing_field():
    engine = TemplateEngine()

    result = engine.render("/电影/{title_cn} ({year}).{ext}", {"title_cn": "测试", "ext": "mkv"})

    assert result.ok is False
    assert result.missing_fields == ["year"]
