from secrets import compare_digest

from fastapi import APIRouter, HTTPException, Request, Response, status
from itsdangerous import BadSignature, URLSafeSerializer
from pydantic import BaseModel

from app.core.config import get_settings

SESSION_COOKIE = "pan115_session"

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthUser(BaseModel):
    username: str


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().session_secret, salt="pan115-session")


def _read_session(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        payload = _serializer().loads(token)
    except BadSignature:
        return None
    if not isinstance(payload, dict):
        return None
    username = payload.get("username")
    if username != get_settings().admin_username:
        return None
    return username


@router.post("/login", response_model=AuthUser)
def login(payload: LoginRequest, response: Response) -> AuthUser:
    settings = get_settings()
    username_ok = compare_digest(payload.username, settings.admin_username)
    password_ok = compare_digest(payload.password, settings.admin_password)
    if not username_ok or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = _serializer().dumps({"username": settings.admin_username})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 7,
    )
    return AuthUser(username=settings.admin_username)


@router.get("/me", response_model=AuthUser)
def me(request: Request) -> AuthUser:
    username = _read_session(request)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return AuthUser(username=username)


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(SESSION_COOKIE)
    return {"status": "ok"}
