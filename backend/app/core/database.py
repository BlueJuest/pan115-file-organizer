from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_db_and_tables() -> None:
    import app.models.operations  # noqa: F401
    import app.models.rules  # noqa: F401
    import app.models.scan  # noqa: F401
    import app.models.settings  # noqa: F401
    import app.models.telegram  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_settings_columns()


def ensure_settings_columns() -> None:
    inspector = inspect(engine)
    if "settings" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("settings")}
    columns = {
        "telegram_bot_token": "VARCHAR(255)",
        "telegram_channel_id": "VARCHAR(100)",
        "default_share_user": "VARCHAR(100) DEFAULT ''",
    }
    with engine.begin() as connection:
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE settings ADD COLUMN {name} {definition}"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
