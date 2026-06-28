from datetime import datetime

from pydantic import BaseModel


class TelegramPushLogRead(BaseModel):
    id: int
    status: str
    telegram_message_id: str
    telegram_channel_id: str
    title: str
    caption: str
    image_url: str
    share_url: str
    source_url: str
    media_type: str
    tmdb_id: int | None
    douban_url: str
    error_message: str
    request_payload: str
    response_payload: str
    resent_from_id: int | None
    created_at: datetime


class TelegramPushLogList(BaseModel):
    items: list[TelegramPushLogRead]
    total: int


class TelegramPushLogDeleteResponse(BaseModel):
    ok: bool
    message: str
