# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import asyncio
from datetime import datetime
from loguru import logger
from .celery_app import celery_app
from ...domain.engine.executor import WorkflowEngine
from ...domain.dsl.registry import registry
from ...infrastructure.db.session import get_sync_session
from ...infrastructure.repositories.sync_workflow_repository import SyncWorkflowRepository

@celery_app.task(name="flowcore.tasks.execute_workflow")
def execute_workflow_task(execution_id: int):
    """
    Celery task to execute a workflow.
    Uses synchronous database access to avoid event loop conflicts.
    """
    logger.info(f"Starting execution of workflow {execution_id}")
    
    session = get_sync_session()
    try:
        repo = SyncWorkflowRepository(session)
        execution = repo.get_execution(execution_id)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return

        workflow_def = registry.get_workflow(execution.workflow_name)
        engine = WorkflowEngine()
        
        try:
            repo.update_execution_status(execution_id, "RUNNING")
            
            # Pure engine logic (simulated iterative execution for MVP)
            # engine.execute_workflow is pure CPU-bound, sync is fine
            final_context = engine.execute_workflow(workflow_def, execution.context)
            
            repo.update_execution_status(execution_id, "COMPLETED", completed_at=datetime.utcnow())
            logger.info(f"Workflow {execution_id} completed successfully")
            
        except Exception as e:
            logger.exception(f"Error executing workflow {execution_id}")
            repo.update_execution_status(execution_id, "FAILED", error=str(e))
            
    finally:
        session.close()

