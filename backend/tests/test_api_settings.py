from fastapi.testclient import TestClient

from app.main import app


def test_settings_round_trip_masks_secrets():
    client = TestClient(app)

    response = client.put(
        "/api/settings",
        json={
            "pan115_cookie": "UID=abc; CID=def; SEID=secret-value",
            "tmdb_api_key": "tmdb-secret-key",
            "tmdb_language": "zh-CN",
            "default_source_dir": "100",
            "default_target_dir": "200",
            "default_recycle_dir": "300",
            "allow_delete_old_files": False,
            "recursive_scan": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pan115_cookie_masked"].startswith("UID=")
    assert "secret-value" not in body["pan115_cookie_masked"]
    assert body["tmdb_api_key_masked"].startswith("tmdb")
    assert "secret-key" not in body["tmdb_api_key_masked"]
    assert body["default_source_dir"] == "100"


def test_test_endpoints_return_not_configured_when_missing_keys():
    client = TestClient(app)

    response_115 = client.post("/api/settings/test-115")
    response_tmdb = client.post("/api/settings/test-tmdb")

    assert response_115.status_code == 200
    assert response_tmdb.status_code == 200
    assert "ok" in response_115.json()
    assert "ok" in response_tmdb.json()
