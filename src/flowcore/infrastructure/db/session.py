# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

def get_database_url() -> str:
    """Returns the async database URL, ensuring it uses the asyncpg driver."""
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://flowcore:flowcore_password@localhost:5432/flowcore_db")
    if "postgresql://" in url and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://")
    if "+psycopg2" in url:
        return url.replace("+psycopg2", "+asyncpg")
    return url

def get_sync_database_url() -> str:
    """Returns the sync database URL, ensuring it uses the psycopg2 driver."""
    url = get_database_url()
    return url.replace("+asyncpg", "+psycopg2")

# --- Async Setup (API) ---
_async_engine = None
_AsyncSessionLocal = None

def get_async_session_local():
    global _async_engine, _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        url = get_database_url()
        _async_engine = create_async_engine(url, echo=False)
        _AsyncSessionLocal = async_sessionmaker(
            bind=_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _AsyncSessionLocal

async def get_db():
    session_factory = get_async_session_local()
    async with session_factory() as session:
        yield session

# --- Sync Setup (Worker) ---
_sync_engine = None
_SyncSessionLocal = None

def get_sync_session_local():
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        url = get_sync_database_url()
        _sync_engine = create_engine(url, echo=False)
        _SyncSessionLocal = sessionmaker(
            bind=_sync_engine,
            expire_on_commit=False,
        )
    return _SyncSessionLocal

def get_sync_session():
    session_factory = get_sync_session_local()
    return session_factory()

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass
