import pytest
from src.flowcore.domain.engine.executor import WorkflowEngine
from src.flowcore.domain.dsl.models import WorkflowDefinition, Step, TaskDefinition
from src.flowcore.domain.dsl.registry import registry
from src.flowcore.adapters.worker.tasks import execute_workflow_task, execute_step_task
from unittest.mock import patch, MagicMock

def test_distributed_execution_flow(caplog):
    # Use loguru's caplog equivalent or just verify behavior via mocks
    # Since Loguru doesn't play well with pytest caplog without extra config,
    # we'll focus on the logic and state changes.
    
    # 1. Register tasks
    def task_a(ctx): return {"a": 1}
    def task_b(ctx): return {"b": 2}
    
    registry.register_task(TaskDefinition(name="task_a", func=task_a))
    registry.register_task(TaskDefinition(name="task_b", func=task_b))
    
    # 2. Define Workflow
    wf_name = "dist_wf"
    wf = WorkflowDefinition(
        name=wf_name,
        steps=[
            Step(name="step_a", task_name="task_a", next_steps=["step_b"]),
            Step(name="step_b", task_name="task_b")
        ]
    )
    registry.register_workflow(wf)
    
    # 3. Mock DB and Celery
    with patch("src.flowcore.adapters.worker.tasks.get_sync_session") as mock_session_factory, \
         patch("src.flowcore.adapters.worker.tasks.execute_step_task.delay") as mock_delay:
        
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session
        
        # Mock Repo behavior
        mock_execution = MagicMock()
        mock_execution.workflow_name = wf_name
        mock_execution.context = {}
        
        with patch("src.flowcore.adapters.worker.tasks.SyncWorkflowRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_execution.return_value = mock_execution
            mock_repo.get_completed_step_names.return_value = set()
            mock_repo.get_step_execution.return_value = None
            
            # Start workflow
            execute_workflow_task(1)
            mock_delay.assert_called_with(1, "step_a")
            
            # Execute step A
            mock_step_exec = MagicMock(id=101)
            mock_repo.create_step_execution.return_value = mock_step_exec
            
            execute_step_task(1, "step_a")
            
            # Should enqueue step_b
            mock_delay.assert_called_with(1, "step_b")
            
            # Should update context with result from task_a
            mock_repo.update_execution_context.assert_called()
            args, _ = mock_repo.update_execution_context.call_args
            assert args[1] == {"a": 1}

def test_simultaneous_workflows():
    # Verify that calling tasks with different IDs works correctly
    wf_name = "sim_wf"
    def task_x(ctx): return {"x": 100}
    registry.register_task(TaskDefinition(name="task_x", func=task_x))
    wf = WorkflowDefinition(name=wf_name, steps=[Step(name="step_x", task_name="task_x")])
    registry.register_workflow(wf)

    with patch("src.flowcore.adapters.worker.tasks.get_sync_session"), \
         patch("src.flowcore.adapters.worker.tasks.SyncWorkflowRepository") as mock_repo_cls, \
         patch("src.flowcore.adapters.worker.tasks.execute_step_task.delay"):
        
        mock_repo = mock_repo_cls.return_value
        
        # Setup for WF 1
        exec1 = MagicMock(workflow_name=wf_name, context={})
        # Setup for WF 2
        exec2 = MagicMock(workflow_name=wf_name, context={})
        
        mock_repo.get_execution.side_effect = [exec1, exec2]
        mock_repo.get_completed_step_names.return_value = set()
        mock_repo.get_step_execution.return_value = None

        # Execute Workflow 1 Step
        execute_step_task(1, "step_x")
        # Execute Workflow 2 Step
        execute_step_task(2, "step_x")
        
        # Both should have been executed independently
        assert mock_repo.get_execution.call_count == 2
        assert mock_repo.create_step_execution.call_count == 2
