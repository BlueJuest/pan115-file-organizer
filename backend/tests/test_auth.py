from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_login_sets_session_cookie_for_configured_admin(monkeypatch):
    monkeypatch.setenv("PAN115_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PAN115_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("PAN115_SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    client = TestClient(app)

    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "secret-pass"}
    )

    assert response.status_code == 200
    assert response.json() == {"username": "admin"}
    assert "pan115_session" in response.cookies

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json() == {"username": "admin"}


def test_login_rejects_wrong_password(monkeypatch):
    monkeypatch.setenv("PAN115_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PAN115_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("PAN115_SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    client = TestClient(app)

    response = client.post("/api/auth/login", json={"username": "admin", "password": "bad"})

    assert response.status_code == 401
    assert response.json() == {"detail": "用户名或密码错误"}


def test_logout_clears_session(monkeypatch):
    monkeypatch.setenv("PAN115_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PAN115_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("PAN115_SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "admin", "password": "secret-pass"})

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401


def test_me_requires_valid_session(monkeypatch):
    monkeypatch.setenv("PAN115_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("PAN115_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("PAN115_SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    client = TestClient(app)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "请先登录"}
