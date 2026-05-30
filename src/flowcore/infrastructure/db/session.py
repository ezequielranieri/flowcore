# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Database URL from environment (Async)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://flowcore:flowcore_password@localhost:5432/flowcore_db")

# Sync Database URL (psycopg2)
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")

# --- Async Setup (API) ---
async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Sync Setup (Worker) ---
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
)

def get_sync_session():
    return SyncSessionLocal()

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

