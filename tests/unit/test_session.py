import pytest
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from flowcore.infrastructure.db import session as db_session_mod
from flowcore.infrastructure.db.session import (
    get_database_url,
    get_sync_database_url,
    get_async_session_local,
    get_db,
    get_sync_session_local,
    get_sync_session
)

@pytest.fixture(autouse=True)
def reset_session_globals():
    db_session_mod._async_engine = None
    db_session_mod._AsyncSessionLocal = None
    db_session_mod._sync_engine = None
    db_session_mod._SyncSessionLocal = None

def test_get_database_url_default(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    expected = "postgresql+asyncpg://flowcore:flowcore_password@localhost:5432/flowcore_db"
    assert get_database_url() == expected

def test_get_database_url_converts_plain_postgresql(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
    assert get_database_url() == "postgresql+asyncpg://user:pass@host/db"

def test_get_database_url_converts_psycopg2(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://user:pass@host/db")
    assert get_database_url() == "postgresql+asyncpg://user:pass@host/db"

def test_get_sync_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host/db")
    assert get_sync_database_url() == "postgresql+psycopg2://user:pass@host/db"

def test_get_async_session_local_is_singleton(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    factory1 = get_async_session_local()
    factory2 = get_async_session_local()
    assert factory1 is factory2
    assert callable(factory1)

@pytest.mark.asyncio
async def test_get_db_yields_session(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    async for session in get_db():
        assert isinstance(session, AsyncSession)

def test_get_sync_session_local_is_singleton(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    factory1 = get_sync_session_local()
    factory2 = get_sync_session_local()
    assert factory1 is factory2
    assert callable(factory1)

def test_get_sync_session_returns_session(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    session = get_sync_session()
    assert isinstance(session, Session)
    session.close()
