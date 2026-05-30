# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import os
import logging
from celery import Celery

# Suppress SQLAlchemy logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "flowcore",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "flowcore.adapters.worker.tasks",
        "flowcore.demo"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

