# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import pytest
from unittest.mock import MagicMock
from flowcore.domain.dsl.models import WorkflowDefinition
from flowcore.domain.dsl.registry import Registry
from flowcore.domain.dsl.exceptions import WorkflowNotFoundError
from flowcore.application.services.workflow_service import WorkflowService

@pytest.fixture
def clean_registry():
    registry = Registry()
    registry.workflows = {}
    registry.tasks = {}
    return registry

def test_registry_stores_multiple_versions(clean_registry):
    v1 = WorkflowDefinition(name="test_wf", version="1.0.0", steps=[])
    v2 = WorkflowDefinition(name="test_wf", version="2.0.0", steps=[])
    
    clean_registry.register_workflow(v1)
    clean_registry.register_workflow(v2)
    
    assert clean_registry.get_workflow("test_wf", "1.0.0") == v1
    assert clean_registry.get_workflow("test_wf", "2.0.0") == v2
    # Default should be latest (last registered)
    assert clean_registry.get_workflow("test_wf") == v2

def test_registry_get_latest_version(clean_registry):
    # Register in non-chronological order
    v1 = WorkflowDefinition(name="test_wf", version="1.0.0", steps=[])
    v3 = WorkflowDefinition(name="test_wf", version="3.0.0", steps=[])
    v2 = WorkflowDefinition(name="test_wf", version="2.0.0", steps=[])
    
    clean_registry.register_workflow(v1)
    clean_registry.register_workflow(v3)
    clean_registry.register_workflow(v2)
    
    # Latest is the last one registered in this implementation
    assert clean_registry.get_latest_version("test_wf") == "2.0.0"
    assert clean_registry.get_workflow("test_wf") == v2

@pytest.mark.asyncio
async def test_execution_stores_workflow_version(clean_registry):
    v1 = WorkflowDefinition(name="test_wf", version="1.0.0", steps=[])
    clean_registry.register_workflow(v1)
    
    mock_repo = MagicMock()
    mock_repo.create_execution = MagicMock()
    # Mocking async create_execution
    async def mock_create(name, context, workflow_version, tenant_id="default"):
        mock_exec = MagicMock()
        mock_exec.id = 1
        return mock_exec
    
    mock_repo.create_execution.side_effect = mock_create
    mock_repo.session = MagicMock()
    mock_repo.session.commit = MagicMock()
    async def mock_commit(): pass
    mock_repo.session.commit.side_effect = mock_commit
    
    service = WorkflowService(mock_repo)
    
    # Start with explicit version
    await service.start_workflow("test_wf", {}, version="1.0.0")
    mock_repo.create_execution.assert_called_with("test_wf", {}, workflow_version="1.0.0", tenant_id="default")
    
    # Start with latest (default)
    await service.start_workflow("test_wf", {})
    mock_repo.create_execution.assert_called_with("test_wf", {}, workflow_version="1.0.0", tenant_id="default")

def test_registry_raises_not_found(clean_registry):
    with pytest.raises(WorkflowNotFoundError):
        clean_registry.get_workflow("non_existent")
    
    v1 = WorkflowDefinition(name="test_wf", version="1.0.0", steps=[])
    clean_registry.register_workflow(v1)
    
    with pytest.raises(WorkflowNotFoundError):
        clean_registry.get_workflow("test_wf", "2.0.0")
