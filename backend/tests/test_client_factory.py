import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.models.base import Base
from app.models.settings import AppSetting
from app.services.client_factory import ClientConfigError, ClientFactory


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_pan115_raises_when_cookie_missing(db_session):
    factory = ClientFactory(db_session)

    with pytest.raises(ClientConfigError, match="未配置 115 Cookie"):
        factory.pan115()


def test_pan115_uses_saved_cookie_with_injected_class(db_session):
    class FakePan115:
        def __init__(self, cookie: str) -> None:
            self.cookie = cookie

    db_session.add(AppSetting(id=1, pan115_cookie="UID=abc; CID=def"))
    db_session.commit()

    client = ClientFactory(db_session, pan115_cls=FakePan115).pan115()

    assert isinstance(client, FakePan115)
    assert client.cookie == "UID=abc; CID=def"


def test_tmdb_returns_none_when_api_key_missing(db_session):
    factory = ClientFactory(db_session)

    assert factory.tmdb() is None
