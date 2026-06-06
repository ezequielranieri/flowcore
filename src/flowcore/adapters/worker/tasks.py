from celery.signals import worker_init

# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import os
from datetime import datetime
from typing import List
from loguru import logger
from .celery_app import celery_app
from ...domain.engine.executor import WorkflowEngine
from ...domain.engine.decision import all_predecessors_completed, determine_next_steps
from ...domain.engine.saga import SagaOrchestrator
from ...domain.dsl.registry import registry
from ...infrastructure.db.session import get_sync_session
from ...infrastructure.repositories.sync_workflow_repository import SyncWorkflowRepository
from ...observability.tracing import setup_tracing

def get_tracer():
    from opentelemetry import trace
    return trace.get_tracer("flowcore-worker")

@worker_init.connect
def on_worker_init(**kwargs):
    """
    Initializes tracing and recovers stuck steps on worker startup.
    """
    setup_tracing("flowcore-worker")
    
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
    except Exception as e:
        logger.error(f"Error during worker recovery: {e}")
    finally:
        session.close()

@celery_app.task(name="flowcore.tasks.execute_workflow")
def execute_workflow_task(execution_id: int):
    """
    Initial task to start a workflow execution.
    Enqueues the first steps as independent tasks.
    """
    from opentelemetry import trace
    logger.info(f"Starting workflow execution {execution_id}")
    
    with get_sync_session() as session:
        try:
            repo = SyncWorkflowRepository(session)
            execution = repo.get_execution(execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return

            with get_tracer().start_as_current_span("workflow.start") as span:
                span.set_attribute("workflow.name", execution.workflow_name)
                span.set_attribute("workflow.execution_id", execution_id)
                
                try:
                    workflow_def = registry.get_workflow(execution.workflow_name, execution.workflow_version)
                    engine = WorkflowEngine()
                    
                    repo.update_execution_status(execution_id, "RUNNING")
                    
                    initial_steps = engine.get_initial_steps(workflow_def)
                    for step in initial_steps:
                        execute_step_task.delay(execution_id, step.name)
                        
                except Exception as e:
                    logger.exception(f"Error starting workflow {execution_id}")
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    try:
                        repo.update_execution_status(execution_id, "FAILED", error=str(e))
                    except:
                        pass
                
        except Exception as e:
            logger.exception(f"Critical error in execute_workflow_task {execution_id}")

@celery_app.task(name="flowcore.tasks.execute_step")
def execute_step_task(execution_id: int, step_name: str):
    """
    Executes a single workflow step.
    Persists state and enqueues next steps.
    """
    from opentelemetry import trace
    import time
    import random
    # Small jitter to reduce race conditions on DB during fan-out
    time.sleep(random.uniform(0.1, 0.5))
    
    logger.info(f"Executing step {step_name} for execution {execution_id}")
    
    with get_sync_session() as session:
        try:
            repo = SyncWorkflowRepository(session)
            execution = repo.get_execution(execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return

            workflow_def = registry.get_workflow(execution.workflow_name, execution.workflow_version)
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
            
            with get_tracer().start_as_current_span("step.execute") as span:
                span.set_attribute("workflow.execution_id", execution_id)
                span.set_attribute("step.name", step_name)
                span.set_attribute("step.task_name", step.task_name if step else "unknown")
                span.set_attribute("worker.id", os.getenv("HOSTNAME", "unknown"))
                
                try:
                    repo.update_step_execution(step_exec.id, "RUNNING")
                    
                    engine = WorkflowEngine()
                    # Execute step logic
                    result = engine.execute_step(step, execution.context)
                    
                    # Update context and step state
                    # Reload execution to get latest context from other parallel steps
                    session.refresh(execution)
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
                        from ...domain.engine.dag import WorkflowDAG
                        dag = WorkflowDAG(workflow_def)
                        # Refresh completed steps set
                        completed = repo.get_completed_step_names(execution_id)
                        if dag.is_workflow_complete(completed):
                             repo.update_execution_status(execution_id, "COMPLETED", completed_at=datetime.utcnow())
                             logger.info(f"Workflow {execution_id} completed successfully")

                    span.set_status(trace.Status(trace.StatusCode.OK))

                except Exception as e:
                    logger.exception(f"Error executing step {step_name}")
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    repo.update_step_execution(step_exec.id, "FAILED", error=str(e))
                    
                    # Saga logic: Check if we should compensate
                    completed_steps = repo.get_completed_step_names(execution_id)
                    saga = SagaOrchestrator()
                    
                    if saga.should_compensate(workflow_def, completed_steps):
                        logger.warning(f"Step {step_name} failed. Triggering Saga compensation.")
                        repo.update_execution_status(execution_id, "COMPENSATING", error=f"Step {step_name} failed: {str(e)}")
                        
                        compensations = saga.get_compensation_steps(workflow_def, completed_steps)
                        for comp_task_name in compensations:
                            try:
                                logger.info(f"Compensating: {comp_task_name}")
                                comp_task = registry.get_task(comp_task_name)
                                # Execute compensation with current context
                                session.refresh(execution)
                                comp_task.func(execution.context)
                            except Exception as ce:
                                logger.error(f"Error executing compensation {comp_task_name}: {ce}")
                        
                        repo.update_execution_status(execution_id, "COMPENSATED")
                    else:
                        repo.update_execution_status(execution_id, "FAILED", error=f"Step {step_name} failed: {str(e)}")
                
        except Exception as e:
            logger.exception(f"Critical error in execute_step_task {execution_id}/{step_name}: {e}")
