from sqlalchemy.orm import Session

from app.clients.pan115 import Pan115Client
from app.clients.tmdb import TmdbClient
from app.models.settings import AppSetting


class ClientConfigError(RuntimeError):
    pass


class ClientFactory:
    def __init__(self, db: Session, pan115_cls=Pan115Client, tmdb_cls=TmdbClient) -> None:
        self.db = db
        self.pan115_cls = pan115_cls
        self.tmdb_cls = tmdb_cls

    def settings(self) -> AppSetting:
        settings = self.db.get(AppSetting, 1)
        if settings is None:
            settings = AppSetting(id=1)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings

    def pan115(self):
        settings = self.settings()
        if not settings.pan115_cookie:
            raise ClientConfigError("未配置 115 Cookie")
        return self.pan115_cls(settings.pan115_cookie)

    def tmdb(self):
        settings = self.settings()
        if not settings.tmdb_api_key:
            return None
        return self.tmdb_cls(settings.tmdb_api_key, settings.tmdb_language)
