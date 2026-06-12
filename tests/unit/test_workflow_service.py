import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from flowcore.application.services.workflow_service import WorkflowService
from flowcore.domain.dsl.exceptions import WorkflowNotFoundError

@pytest.mark.asyncio
async def test_start_workflow_raises_when_workflow_def_is_none():
    repo = MagicMock()
    service = WorkflowService(repository=repo)
    
    with patch("flowcore.application.services.workflow_service.registry.get_workflow", return_value=None):
        with pytest.raises(WorkflowNotFoundError):
            await service.start_workflow("some_wf", {}, version="1.0.0")

@pytest.mark.asyncio
async def test_start_workflow_enqueues_celery_task():
    repo = MagicMock()
    execution = MagicMock()
    execution.id = 42
    repo.create_execution = AsyncMock(return_value=execution)
    repo.session.commit = AsyncMock()
    
    celery_app = MagicMock()
    service = WorkflowService(repository=repo, celery_app=celery_app)
    
    with patch("flowcore.application.services.workflow_service.registry.get_workflow", return_value=MagicMock()):
        result = await service.start_workflow("some_wf", {}, version="1.0.0")
        
    assert result == 42
    celery_app.send_task.assert_called_once_with(
        "flowcore.tasks.execute_workflow",
        args=[42],
        kwargs={}
    )
