from celery.signals import worker_init

# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import os
from datetime import datetime
from typing import List
from loguru import logger
from .celery_app import celery_app
from ...domain.engine.executor import WorkflowEngine
from ...domain.engine.decision import all_predecessors_completed, determine_next_steps
from ...domain.dsl.registry import registry
from ...infrastructure.db.session import get_sync_session
from ...infrastructure.repositories.sync_workflow_repository import SyncWorkflowRepository

@worker_init.connect
def recover_stuck_steps(**kwargs):
    timeout = int(os.getenv("STUCK_STEP_TIMEOUT_MINUTES", "15"))
    logger.info(f"Worker startup: checking for stuck steps with timeout {timeout} minutes")
    
    session = get_sync_session()
    try:
        repo = SyncWorkflowRepository(session)
        stuck_steps = repo.get_stuck_steps(timeout)
        for step in stuck_steps:
            logger.warning(f"Found stuck step {step.id} (name: {step.step_name}), resetting to PENDING")
            repo.reset_step_status(step.id)
        logger.info(f"Worker startup: recovery complete, {len(stuck_steps)} steps reset")
    finally:
        session.close()

@celery_app.task(name="flowcore.tasks.execute_workflow")
def execute_workflow_task(execution_id: int):
    """
    Initial task to start a workflow execution.
    Enqueues the first steps as independent tasks.
    """
    logger.info(f"Starting workflow execution {execution_id}")
    
    session = get_sync_session()
    try:
        repo = SyncWorkflowRepository(session)
        execution = repo.get_execution(execution_id)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return

        workflow_def = registry.get_workflow(execution.workflow_name)
        engine = WorkflowEngine()
        
        repo.update_execution_status(execution_id, "RUNNING")
        
        initial_steps = engine.get_initial_steps(workflow_def)
        for step in initial_steps:
            execute_step_task.delay(execution_id, step.name)
            
    except Exception as e:
        logger.exception(f"Error starting workflow {execution_id}")
        repo.update_execution_status(execution_id, "FAILED", error=str(e))
    finally:
        session.close()

@celery_app.task(name="flowcore.tasks.execute_step")
def execute_step_task(execution_id: int, step_name: str):
    """
    Executes a single workflow step.
    Persists state and enqueues next steps.
    """
    logger.info(f"Executing step {step_name} for execution {execution_id}")
    
    session = get_sync_session()
    try:
        repo = SyncWorkflowRepository(session)
        execution = repo.get_execution(execution_id)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return

        workflow_def = registry.get_workflow(execution.workflow_name)
        step = next((s for s in workflow_def.steps if s.name == step_name), None)
        if not step:
            logger.error(f"Step {step_name} not found in workflow {execution.workflow_name}")
            return

        # Check predecessors
        completed_steps = repo.get_completed_step_names(execution_id)
        if not all_predecessors_completed(step, completed_steps):
            logger.info(f"Step {step_name} is waiting for predecessors")
            return

        # Check if already running or completed
        step_exec = repo.get_step_execution(execution_id, step_name)
        if step_exec and step_exec.status in ["RUNNING", "COMPLETED"]:
            logger.info(f"Step {step_name} already {step_exec.status}")
            return

        if not step_exec:
            step_exec = repo.create_step_execution(execution_id, step_name, execution.context)
        
        try:
            repo.update_step_execution(step_exec.id, "RUNNING")
            
            engine = WorkflowEngine()
            # Execute step logic
            result = engine.execute_step(step, execution.context)
            
            # Update context and step state
            new_context = execution.context.copy()
            new_context.update(result)
            repo.update_execution_context(execution_id, new_context)
            repo.update_step_execution(step_exec.id, "COMPLETED", output_data=result)
            
            # Determine next steps
            next_step_names = determine_next_steps(step, new_context)
            for next_name in next_step_names:
                execute_step_task.delay(execution_id, next_name)
            
            # Check if workflow is complete
            if not next_step_names:
                # This is a bit simplified; we should check if all branches are done.
                # For Phase 2, we check if there are any other pending/running steps.
                # But for now, if this branch ends, we might be done.
                # A better way is to check the full DAG completion.
                all_steps_completed = repo.get_completed_step_names(execution_id)
                if len(all_steps_completed) == len(workflow_def.steps):
                     repo.update_execution_status(execution_id, "COMPLETED", completed_at=datetime.utcnow())
                     logger.info(f"Workflow {execution_id} completed successfully")

        except Exception as e:
            logger.exception(f"Error executing step {step_name}")
            repo.update_step_execution(step_exec.id, "FAILED", error=str(e))
            repo.update_execution_status(execution_id, "FAILED", error=f"Step {step_name} failed: {str(e)}")
            
    finally:
        session.close()
