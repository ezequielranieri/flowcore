# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import pytest
from unittest.mock import MagicMock, AsyncMock
from flowcore.infrastructure.repositories.workflow_repository import WorkflowRepository
from flowcore.infrastructure.db.models import WorkflowExecution

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def repo(mock_session):
    return WorkflowRepository(mock_session)

@pytest.mark.asyncio
async def test_executions_isolated_by_tenant(repo, mock_session):
    # Setup mock return value for list_executions
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    
    # Use AsyncMock for execute
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    await repo.list_executions(limit=20, tenant_id="tenant_a")
    
    # Verify that the query included tenant_id filtering
    args, kwargs = mock_session.execute.call_args
    query = args[0]
    # This is a bit internal but verifies the where clause
    assert "workflow_executions.tenant_id = :tenant_id_1" in str(query)

@pytest.mark.asyncio
async def test_get_execution_wrong_tenant_returns_none(repo, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    result = await repo.get_execution(execution_id=1, tenant_id="wrong_tenant")
    
    assert result is None
    args, kwargs = mock_session.execute.call_args
    query = args[0]
    assert "workflow_executions.tenant_id = :tenant_id_1" in str(query)

@pytest.mark.asyncio
async def test_default_tenant_backward_compatible(repo, mock_session):
    # Mocking flush to not fail
    mock_session.flush = AsyncMock()
    
    execution = await repo.create_execution(
        workflow_name="test_wf",
        context={}
    )
    
    # Should default to "default" if not specified
    assert execution.tenant_id == "default"
    assert execution.workflow_name == "test_wf"
