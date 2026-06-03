# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import os
import pytest
import threading
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def reset_db_engines():
    """Resets engines before each test to ensure isolation."""
    import flowcore.infrastructure.db.session as db_session_mod
    db_session_mod._async_engine = None
    db_session_mod._AsyncSessionLocal = None
    db_session_mod._sync_engine = None
    db_session_mod._SyncSessionLocal = None

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as postgres:
        host = postgres.get_container_host_ip()
        port = postgres.get_exposed_port(5432)
        user = postgres.username
        password = postgres.password
        db = postgres.dbname
        
        async_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        sync_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
        
        os.environ["DATABASE_URL"] = async_url
        yield sync_url

@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(6379)
        url = f"redis://{host}:{port}/0"
        os.environ["CELERY_BROKER_URL"] = url
        yield url

@pytest.fixture(scope="session")
def db_setup(postgres_container):
    """Initializes the database schema using Alembic."""
    sync_url = postgres_container
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(alembic_cfg, "head")
    return sync_url

@pytest.fixture
def db_session(db_setup):
    """Provides a synchronous session and cleans up after each test."""
    engine = create_engine(db_setup)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    
    from flowcore.infrastructure.db.models import Base
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()

@pytest.fixture(scope="session")
def workflow_registry():
    """Ensures workflows are registered."""
    from flowcore.domain.dsl.registry import registry
    from flowcore import demo
    return registry

@pytest.fixture(scope="session")
def celery_config(redis_container, postgres_container, workflow_registry):
    """Configures the Celery app for testing."""
    from flowcore.adapters.worker.celery_app import celery_app
    celery_app.conf.broker_url = os.environ["CELERY_BROKER_URL"]
    celery_app.conf.result_backend = os.environ["CELERY_BROKER_URL"]
    # Disable task execution during testing if we want to control it, 
    # but here we want a real worker.
    return celery_app

@pytest.fixture(scope="session")
def celery_worker(celery_config, db_setup):
    """Starts a real Celery worker in a separate thread."""
    # Note: On Windows, solo pool is often more stable for this kind of test.
    worker = celery_config.Worker(pool='solo', loglevel='info')
    t = threading.Thread(target=worker.start, daemon=True)
    t.start()
    # Give it a bit to start
    import time
    time.sleep(2)
    yield worker
    worker.stop()

@pytest.fixture
def api_client(celery_config, db_setup):
    """Provides a TestClient for the FastAPI app."""
    from flowcore.adapters.api.main import app
    with TestClient(app) as client:
        yield client
