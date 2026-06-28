from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

import app.api.submissions as submissions_api
from app.core.config import get_settings
from app.core.database import get_db
from app.models import AppSetting, TelegramPushLog
from app.schemas.submissions import SubmissionPublishResponse
from app.schemas.telegram import TelegramPushLogDeleteResponse, TelegramPushLogList, TelegramPushLogRead

router = APIRouter(prefix="/api/telegram-push-logs", tags=["telegram-push-logs"])


def to_read(log: TelegramPushLog) -> TelegramPushLogRead:
    return TelegramPushLogRead(
        id=log.id,
        status=log.status,
        telegram_message_id=log.telegram_message_id,
        telegram_channel_id=log.telegram_channel_id,
        title=log.title,
        caption=log.caption,
        image_url=log.image_url,
        share_url=log.share_url,
        source_url=log.source_url,
        media_type=log.media_type,
        tmdb_id=log.tmdb_id,
        douban_url=log.douban_url,
        error_message=log.error_message,
        request_payload=log.request_payload,
        response_payload=log.response_payload,
        resent_from_id=log.resent_from_id,
        created_at=log.created_at,
    )


@router.get("", response_model=TelegramPushLogList)
def list_telegram_push_logs(
    status: str = "",
    keyword: str = "",
    channel_id: str = "",
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> TelegramPushLogList:
    conditions = []
    if status:
        conditions.append(TelegramPushLog.status == status)
    if channel_id:
        conditions.append(TelegramPushLog.telegram_channel_id == channel_id)
    if start_at is not None:
        conditions.append(TelegramPushLog.created_at >= start_at)
    if end_at is not None:
        conditions.append(TelegramPushLog.created_at <= end_at)
    if keyword:
        pattern = f"%{keyword}%"
        conditions.append(
            or_(
                TelegramPushLog.title.like(pattern),
                TelegramPushLog.caption.like(pattern),
                TelegramPushLog.share_url.like(pattern),
                TelegramPushLog.source_url.like(pattern),
                TelegramPushLog.error_message.like(pattern),
            )
        )

    query = select(TelegramPushLog)
    count_query = select(func.count()).select_from(TelegramPushLog)
    for condition in conditions:
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.scalar(count_query) or 0
    logs = db.scalars(query.order_by(TelegramPushLog.id.desc()).offset(offset).limit(limit)).all()
    return TelegramPushLogList(items=[to_read(log) for log in logs], total=total)


@router.post("/{log_id}/resend", response_model=SubmissionPublishResponse)
def resend_telegram_push_log(log_id: int, db: Session = Depends(get_db)) -> SubmissionPublishResponse:
    source = db.get(TelegramPushLog, log_id)
    if source is None:
        raise HTTPException(status_code=404, detail="推送记录不存在")
    bot_token, fallback_channel_id = _telegram_config(db)
    channel_id = source.telegram_channel_id or fallback_channel_id
    if not bot_token or not channel_id:
        raise HTTPException(status_code=400, detail="未配置 Telegram Bot Token 或频道 ID")

    log = TelegramPushLog(
        status="pending",
        telegram_channel_id=channel_id,
        title=source.title,
        caption=source.caption,
        image_url=source.image_url,
        share_url=source.share_url,
        source_url=source.source_url,
        media_type=source.media_type,
        tmdb_id=source.tmdb_id,
        douban_url=source.douban_url,
        request_payload=source.request_payload,
        resent_from_id=source.id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        message_id = submissions_api.TELEGRAM_CLIENT_CLASS(bot_token, channel_id).send_photo(
            source.image_url,
            source.caption,
        )
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)
        db.add(log)
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log.status = "success"
    log.telegram_message_id = message_id
    log.response_payload = f"telegram_message_id={message_id}"
    db.add(log)
    db.commit()
    return SubmissionPublishResponse(ok=True, message="Telegram 重新推送成功", telegram_message_id=message_id)


@router.delete("/{log_id}", response_model=TelegramPushLogDeleteResponse)
def delete_telegram_push_log(log_id: int, db: Session = Depends(get_db)) -> TelegramPushLogDeleteResponse:
    log = db.get(TelegramPushLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="推送记录不存在")
    db.delete(log)
    db.commit()
    return TelegramPushLogDeleteResponse(ok=True, message="推送记录已删除")


def _telegram_config(db: Session) -> tuple[str, str]:
    settings = db.get(AppSetting, 1)
    app_settings = get_settings()
    bot_token = (settings.telegram_bot_token if settings else "") or app_settings.telegram_bot_token
    channel_id = (settings.telegram_channel_id if settings else "") or app_settings.telegram_channel_id
    return bot_token or "", channel_id or ""
