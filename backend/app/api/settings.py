import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.clients.pan115 import Pan115Client
from app.clients.tmdb import TmdbClient
from app.core.database import get_db
from app.core.security import mask_secret
from app.models.settings import AppSetting
from app.schemas.common import TestResult
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services.client_factory import ClientConfigError, ClientFactory

PAN115_CLIENT_CLASS = Pan115Client
TMDB_CLIENT_CLASS = TmdbClient

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_or_create_settings(db: Session) -> AppSetting:
    settings = db.get(AppSetting, 1)
    if settings is None:
        settings = AppSetting(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def to_read(settings: AppSetting) -> SettingsRead:
    return SettingsRead(
        pan115_cookie_masked=mask_secret(settings.pan115_cookie),
        tmdb_api_key_masked=mask_secret(settings.tmdb_api_key),
        tmdb_language=settings.tmdb_language,
        telegram_bot_token_masked=mask_secret(settings.telegram_bot_token),
        telegram_channel_id=settings.telegram_channel_id or "",
        default_share_user=settings.default_share_user or "",
        default_source_dir=settings.default_source_dir,
        default_target_dir=settings.default_target_dir,
        default_recycle_dir=settings.default_recycle_dir,
        allow_delete_old_files=bool(settings.allow_delete_old_files),
        recursive_scan=bool(settings.recursive_scan),
    )


@router.get("", response_model=SettingsRead)
def read_settings(db: Session = Depends(get_db)) -> SettingsRead:
    settings = get_or_create_settings(db)
    return to_read(settings)


@router.put("", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)) -> SettingsRead:
    settings = get_or_create_settings(db)
    if payload.pan115_cookie:
        settings.pan115_cookie = payload.pan115_cookie
    if payload.tmdb_api_key:
        settings.tmdb_api_key = payload.tmdb_api_key
    if payload.telegram_bot_token:
        settings.telegram_bot_token = payload.telegram_bot_token
    if payload.telegram_channel_id:
        settings.telegram_channel_id = payload.telegram_channel_id
    settings.tmdb_language = payload.tmdb_language
    settings.default_share_user = payload.default_share_user
    settings.default_source_dir = payload.default_source_dir
    settings.default_target_dir = payload.default_target_dir
    settings.default_recycle_dir = payload.default_recycle_dir
    settings.allow_delete_old_files = int(payload.allow_delete_old_files)
    settings.recursive_scan = int(payload.recursive_scan)

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return to_read(settings)


@router.post("/test-115", response_model=TestResult)
def test_115(db: Session = Depends(get_db)) -> TestResult:
    try:
        ok = ClientFactory(db, pan115_cls=PAN115_CLIENT_CLASS).pan115().test_connection()
    except ClientConfigError as exc:
        return TestResult(ok=False, message=str(exc))
    except Exception:
        return TestResult(ok=False, message="115 连接失败")
    if not ok:
        return TestResult(ok=False, message="115 连接失败")
    return TestResult(ok=True, message="115 连接成功")


@router.post("/test-tmdb", response_model=TestResult)
def test_tmdb(db: Session = Depends(get_db)) -> TestResult:
    client = ClientFactory(db, tmdb_cls=TMDB_CLIENT_CLASS).tmdb()
    if client is None:
        return TestResult(ok=False, message="未配置 TMDB API Key")
    try:
        client.search_movie("test", None)
    except httpx.HTTPStatusError as exc:
        return TestResult(ok=False, message=f"TMDB 连接失败: HTTP {exc.response.status_code}")
    except httpx.TimeoutException:
        return TestResult(ok=False, message="TMDB 连接失败: Timeout")
    except httpx.RequestError as exc:
        return TestResult(ok=False, message=f"TMDB 连接失败: {exc.__class__.__name__}: {exc}")
    except Exception as exc:
        return TestResult(ok=False, message=f"TMDB 连接失败: {exc.__class__.__name__}")
    return TestResult(ok=True, message="TMDB 连接成功")
