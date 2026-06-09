from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import mask_secret
from app.models.settings import AppSetting
from app.schemas.common import TestResult
from app.schemas.settings import SettingsRead, SettingsUpdate

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
    settings.pan115_cookie = payload.pan115_cookie
    settings.tmdb_api_key = payload.tmdb_api_key
    settings.tmdb_language = payload.tmdb_language
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
    settings = get_or_create_settings(db)
    if not settings.pan115_cookie:
        return TestResult(ok=False, message="115 cookie 未配置")
    return TestResult(ok=True, message="115 cookie 已配置")


@router.post("/test-tmdb", response_model=TestResult)
def test_tmdb(db: Session = Depends(get_db)) -> TestResult:
    settings = get_or_create_settings(db)
    if not settings.tmdb_api_key:
        return TestResult(ok=False, message="TMDB API key 未配置")
    return TestResult(ok=True, message="TMDB API key 已配置")
