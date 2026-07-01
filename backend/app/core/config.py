from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = "115 文件整理"
    database_url: str = "sqlite:///../data/app.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    data_dir: Path = Path("../data")
    telegram_bot_token: str = ""
    telegram_channel_id: str = ""
    admin_username: str = "root"
    admin_password: str = "Dl960513."
    session_secret: str = "change-me-in-production"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="PAN115_")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
