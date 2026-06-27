from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    pan115_cookie: str | None = None
    tmdb_api_key: str | None = None
    tmdb_language: str = "zh-CN"
    telegram_bot_token: str | None = None
    telegram_channel_id: str | None = None
    default_share_user: str = ""
    default_source_dir: str = "0"
    default_target_dir: str = "0"
    default_recycle_dir: str = "0"
    allow_delete_old_files: bool = False
    recursive_scan: bool = True


class SettingsRead(BaseModel):
    pan115_cookie_masked: str
    tmdb_api_key_masked: str
    tmdb_language: str
    telegram_bot_token_masked: str
    telegram_channel_id: str
    default_share_user: str
    default_source_dir: str
    default_target_dir: str
    default_recycle_dir: str
    allow_delete_old_files: bool
    recursive_scan: bool
