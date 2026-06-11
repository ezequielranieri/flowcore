# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import pytest
from unittest.mock import MagicMock
from flowcore.infrastructure.repositories.sync_workflow_repository import SyncWorkflowRepository
from flowcore.infrastructure.db.models import WorkflowExecution, StepExecution

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def repo(mock_session):
    return SyncWorkflowRepository(mock_session)

def test_complete_step_atomically_updates_both_tables(repo, mock_session):
    step_id = 1
    execution_id = 10
    output_data = {"result": "ok"}
    new_context = {"data": 123}
    
    repo.complete_step_atomically(step_id, execution_id, output_data, new_context)
    
    # Should have executed two updates
    assert mock_session.execute.call_count == 2
    # Should have committed once
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()

def test_complete_step_atomically_rolls_back_on_failure(repo, mock_session):
    step_id = 1
    execution_id = 10
    
    # Simulate failure on the second execute call
    mock_session.execute.side_effect = [None, Exception("DB Error")]
    
    with pytest.raises(Exception, match="DB Error"):
        repo.complete_step_atomically(step_id, execution_id, {}, {})
    
    # Should have called rollback
    mock_session.rollback.assert_called_once()
    # Should NOT have committed
    mock_session.commit.assert_not_called()

def test_fail_step_atomically_updates_both_tables(repo, mock_session):
    step_id = 1
    execution_id = 10
    error_msg = "Something went wrong"
    
    repo.fail_step_atomically(step_id, execution_id, error_msg)
    
    # Should have executed two updates
    assert mock_session.execute.call_count == 2
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()

def test_start_step_atomically(repo, mock_session):
    step_id = 1
    repo.start_step_atomically(step_id)
    
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

def test_get_completed_step_names(repo, mock_session):
    execution_id = 10
    mock_result = MagicMock()
    mock_result.all.return_value = [("step1",), ("step2",)]
    mock_session.execute.return_value = mock_result
    
    names = repo.get_completed_step_names(execution_id)
    
    assert names == {"step1", "step2"}
    mock_session.execute.assert_called_once()

def test_get_stuck_steps(repo, mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    steps = repo.get_stuck_steps(15)
    assert steps == []
    mock_session.execute.assert_called_once()

def test_reset_step_status(repo, mock_session):
    repo.reset_step_status(1)
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

def test_update_execution_status(repo, mock_session):
    repo.update_execution_status(1, "RUNNING")
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

def test_update_execution_context(repo, mock_session):
    repo.update_execution_context(1, {"new": "data"})
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

def test_create_step_execution(repo, mock_session):
    repo.create_step_execution(1, "step_name", {"input": 1})
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
