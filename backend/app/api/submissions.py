from html import escape
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.clients.douban import DoubanClient
from app.clients.share115 import Share115Client, ShareInspection
from app.clients.telegram import TelegramClient
from app.clients.tmdb import TmdbClient
from app.core.config import get_settings
from app.core.database import get_db
from app.models import TelegramPushLog
from app.models.settings import AppSetting
from app.schemas.submissions import (
    SubmissionMediaDetails,
    SubmissionPreviewRequest,
    SubmissionPreviewResponse,
    SubmissionPublishRequest,
    SubmissionPublishResponse,
)
from app.services.submission_parser import format_size, parse_submission_folder_name

router = APIRouter(prefix="/api/submissions", tags=["submissions"])

SHARE_CLIENT_CLASS = Share115Client
TMDB_CLIENT_CLASS = TmdbClient
TELEGRAM_CLIENT_CLASS = TelegramClient
DOUBAN_CLIENT_CLASS = DoubanClient
FIXED_SHARE_USER = "MeiOvO"
FIXED_SHARE_USER_URL = "https://t.me/MeiOvO"


@router.post("/preview", response_model=SubmissionPreviewResponse)
def preview_submission(
    payload: SubmissionPreviewRequest,
    db: Session = Depends(get_db),
) -> SubmissionPreviewResponse:
    settings = _settings(db)
    if not settings.tmdb_api_key:
        raise HTTPException(status_code=400, detail="未配置 TMDB API Key")

    try:
        inspection = SHARE_CLIENT_CLASS().inspect_share(payload.share_url, payload.receive_code)
        parsed = parse_submission_folder_name(inspection.folder_name)
        media = _resolve_tmdb(settings, parsed.tmdb_id, payload.media_type)
        douban_rating, douban_url = _resolve_douban(media, parsed.year)
        size_text = format_size(inspection.total_size)
        image_url = _tmdb_image_url(media)
        share_user = inspection.share_user or FIXED_SHARE_USER
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SubmissionPreviewResponse(
        share_url=payload.share_url,
        receive_code=payload.receive_code,
        folder_name=inspection.folder_name,
        parsed_title=parsed.title,
        parsed_year=parsed.year,
        media=media,
        quality=payload.quality,
        video_source=payload.video_source,
        subtitles=payload.subtitles,
        custom_content=payload.custom_content,
        share_user=share_user,
        share_user_url=FIXED_SHARE_USER_URL,
        douban_rating=douban_rating,
        douban_url=douban_url,
        total_size=inspection.total_size,
        size_text=size_text,
        image_url=image_url,
        caption=_caption(media, payload, size_text, douban_rating, douban_url, share_user),
    )


@router.post("/publish", response_model=SubmissionPublishResponse)
def publish_submission(
    payload: SubmissionPublishRequest,
    db: Session = Depends(get_db),
) -> SubmissionPublishResponse:
    settings = _settings(db)
    app_settings = get_settings()
    bot_token = settings.telegram_bot_token or app_settings.telegram_bot_token
    channel_id = settings.telegram_channel_id or app_settings.telegram_channel_id
    if not bot_token or not channel_id:
        raise HTTPException(status_code=400, detail="未配置 Telegram Bot Token 或频道 ID")

    log = TelegramPushLog(
        status="pending",
        telegram_channel_id=channel_id,
        title=_title_from_caption(payload.caption),
        caption=payload.caption,
        image_url=payload.image_url,
        share_url=_share_url_from_caption(payload.caption),
        source_url=_share_url_from_caption(payload.caption),
        request_payload=f"image_url={payload.image_url}",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        message_id = TELEGRAM_CLIENT_CLASS(bot_token, channel_id).send_photo(payload.image_url, payload.caption)
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
    return SubmissionPublishResponse(ok=True, message="Telegram 推送成功", telegram_message_id=message_id)


def _settings(db: Session) -> AppSetting:
    settings = db.get(AppSetting, 1)
    if settings is None:
        settings = AppSetting(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _title_from_caption(caption: str) -> str:
    marker = "<b>"
    end_marker = "</b>"
    start = caption.find(marker)
    end = caption.find(end_marker, start + len(marker))
    if start == -1 or end == -1:
        return ""
    return caption[start + len(marker) : end].strip()


def _share_url_from_caption(caption: str) -> str:
    marker = "href=\""
    search_from = caption.find("115")
    if search_from == -1:
        search_from = 0
    start = caption.rfind(marker, 0, search_from)
    if start == -1:
        start = caption.find(marker)
    if start == -1:
        return ""
    value_start = start + len(marker)
    value_end = caption.find("\"", value_start)
    if value_end == -1:
        return ""
    return caption[value_start:value_end]


def _resolve_tmdb(settings: AppSetting, tmdb_id: int, media_type: str = "auto") -> SubmissionMediaDetails:
    client = TMDB_CLIENT_CLASS(settings.tmdb_api_key or "", settings.tmdb_language)
    last_error: Exception | None = None
    media_types = ("movie", "tv") if media_type == "auto" else (media_type,)
    for current_type in media_types:
        try:
            details = client.get_details(tmdb_id, current_type)
        except Exception as exc:
            last_error = exc
            continue
        if details is not None:
            return _to_media_details(details, tmdb_id, current_type)
    if last_error is not None:
        raise last_error
    if media_type == "movie":
        raise ValueError("TMDB 未找到对应电影")
    if media_type == "tv":
        raise ValueError("TMDB 未找到对应剧集")
    raise ValueError("TMDB 未找到对应电影或剧集")


def _to_media_details(details: Any, tmdb_id: int, fallback_type: str) -> SubmissionMediaDetails:
    if isinstance(details, SubmissionMediaDetails):
        return details
    if isinstance(details, dict):
        title = details.get("title") or details.get("name") or ""
        original_title = details.get("original_title") or details.get("original_name") or title
        date_value = details.get("release_date") or details.get("first_air_date") or ""
        genres = [str(item.get("name")) for item in details.get("genres", []) if item.get("name")]
        return SubmissionMediaDetails(
            tmdb_id=int(details.get("id") or tmdb_id),
            media_type=fallback_type,
            title=title,
            original_title=original_title,
            year=_year(date_value),
            overview=details.get("overview") or "",
            poster_path=details.get("poster_path") or "",
            backdrop_path=details.get("backdrop_path") or "",
            vote_average=details.get("vote_average"),
            genres=genres,
        )
    return SubmissionMediaDetails(
        tmdb_id=getattr(details, "tmdb_id", tmdb_id),
        media_type=getattr(details, "media_type", fallback_type),
        title=getattr(details, "title_cn", "") or getattr(details, "title", ""),
        original_title=getattr(details, "title_original", "") or getattr(details, "original_title", ""),
        year=getattr(details, "year", None),
        overview=getattr(details, "overview", ""),
        poster_path=getattr(details, "poster_path", ""),
        backdrop_path=getattr(details, "backdrop_path", ""),
        vote_average=getattr(details, "vote_average", None),
        genres=getattr(details, "genres", None) or [],
    )


def _year(value: str) -> int | None:
    if len(value) < 4:
        return None
    try:
        return int(value[:4])
    except ValueError:
        return None


def _resolve_douban(media: SubmissionMediaDetails, parsed_year: int | None) -> tuple[str, str]:
    try:
        match = DOUBAN_CLIENT_CLASS().search(media.title, media.year or parsed_year)
    except Exception:
        return "", ""
    if match is None:
        return "", ""
    return match.rating, match.url


def _tmdb_image_url(media: SubmissionMediaDetails) -> str:
    path = media.backdrop_path or media.poster_path
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return f"https://image.tmdb.org/t/p/original{path}"


def _caption(
    media: SubmissionMediaDetails,
    payload: SubmissionPreviewRequest,
    size_text: str,
    douban_rating: str,
    douban_url: str,
    share_user: str,
) -> str:
    year = f" ({media.year})" if media.year else ""
    media_label = "电影" if media.media_type == "movie" else "剧集"
    tmdb_url = f"https://www.themoviedb.org/{media.media_type}/{media.tmdb_id}"
    lines = [
        f"📽️ <b>{escape(media.title)}{year}</b>",
        "",
        f"🎬 类型：{media_label}",
    ]
    if media.vote_average is not None:
        lines.append(f'⭐️ TMDB评分：<a href="{tmdb_url}">{media.vote_average:.1f}/10</a>')
    else:
        lines.append(f'⭐️ TMDB：<a href="{tmdb_url}">{media.tmdb_id}</a>')
    if douban_rating or douban_url:
        rating = escape(douban_rating or "暂无评分")
        url = escape(douban_url, quote=True)
        if douban_url and douban_rating:
            lines.append(f'🍿 豆瓣评分：<a href="{url}">{rating}</a>')
        elif douban_url:
            lines.append(f'🍿 豆瓣：<a href="{url}">{rating}</a>')
        else:
            lines.append(f"🍿 豆瓣评分：{rating}")
    if payload.quality:
        lines.append(f"📺 画质：{escape(payload.quality)}")
    if payload.video_source:
        lines.append(f"📼 视频：{escape(payload.video_source)}")
    if payload.subtitles:
        lines.append(f"💬 字幕：{escape(payload.subtitles)}")
    if size_text:
        lines.append(f"💾 大小：{escape(size_text)}")
    lines.append(f'👤 分享：<a href="{FIXED_SHARE_USER_URL}">{escape(share_user)}</a>')
    if payload.custom_content:
        lines.extend([f"<blockquote><b>{escape(payload.custom_content)}</b></blockquote>", ""])
    else:
        lines.append("")
    lines.append(f'🔗 链接：<a href="{escape(payload.share_url, quote=True)}">115网盘</a>')
    if media.overview:
        lines.extend(["", "📖 简介：", f"<blockquote>{escape(media.overview)}</blockquote>"])
    tags = [media.title, *media.genres]
    if tags:
        tag_text = " ".join(f"#{tag.replace(' ', '')}" for tag in tags if tag)
        lines.extend(["", f"🏷 标签：{escape(tag_text)}"])
    return "\n".join(lines)
