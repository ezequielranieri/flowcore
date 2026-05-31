# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import os
import logging
import importlib
import pkgutil
from celery import Celery
from celery.signals import worker_init
from loguru import logger

# Suppress SQLAlchemy logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "flowcore",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "flowcore.adapters.worker.tasks"
    ]
)

@worker_init.connect
def autodiscover_workflows(**kwargs):
    """
    Recursively discovers and imports modules containing @task or @workflow.
    """
    from ...domain.dsl.registry import registry
    
    # We search from the project root (src)
    # The package structure is flowcore.xxx
    start_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    base_package = "flowcore"
    
    logger.info("Worker startup: starting auto-discovery of workflows and tasks")
    
    discovered_count = 0
    # Walk through the directory src/flowcore
    flowcore_path = os.path.join(start_path, "flowcore")
    
    for root, dirs, files in os.walk(flowcore_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = os.path.join(root, file)
                
                # Check if file contains @task or @workflow
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "@task" in content or "@workflow" in content:
                        # Convert path to module name
                        relative_path = os.path.relpath(full_path, start_path)
                        module_name = relative_path.replace(os.path.sep, ".").removesuffix(".py")
                        
                        try:
                            importlib.import_module(module_name)
                            discovered_count += 1
                        except Exception as e:
                            logger.error(f"Failed to import module {module_name}: {e}")
    
    logger.info(f"Auto-discovery complete: {discovered_count} modules imported. "
                f"Registry now has {len(registry.workflows)} workflows and {len(registry.tasks)} tasks.")

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

