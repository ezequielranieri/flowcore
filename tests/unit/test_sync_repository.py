import pytest
from flowcore.infrastructure.repositories.sync_workflow_repository import SyncWorkflowRepository
from flowcore.infrastructure.db.models import WorkflowExecution, StepExecution, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from datetime import datetime, UTC

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_get_step_execution_found_and_not_found(db_session):
    repo = SyncWorkflowRepository(db_session)
    execution = WorkflowExecution(workflow_name="test", status="PENDING", context={})
    db_session.add(execution)
    db_session.commit()
    
    step = StepExecution(workflow_execution_id=execution.id, step_name="my_step", status="PENDING")
    db_session.add(step)
    db_session.commit()
    
    found = repo.get_step_execution(execution.id, "my_step")
    assert found is not None
    assert found.step_name == "my_step"
    
    not_found = repo.get_step_execution(execution.id, "nonexistent")
    assert not_found is None

def test_update_step_execution(db_session):
    repo = SyncWorkflowRepository(db_session)
    execution = WorkflowExecution(workflow_name="test", status="PENDING", context={})
    db_session.add(execution)
    db_session.commit()
    
    step = StepExecution(workflow_execution_id=execution.id, step_name="my_step", status="RUNNING")
    db_session.add(step)
    db_session.commit()
    
    repo.update_step_execution(step.id, status="COMPLETED", output_data={"ok": True})
    
    db_session.refresh(step)
    assert step.status == "COMPLETED"
    assert step.output_data == {"ok": True}
    assert step.completed_at is not None

def test_update_step_execution_with_error_no_output(db_session):
    repo = SyncWorkflowRepository(db_session)
    execution = WorkflowExecution(workflow_name="test", status="PENDING", context={})
    db_session.add(execution)
    db_session.commit()
    
    step = StepExecution(workflow_execution_id=execution.id, step_name="my_step", status="RUNNING")
    db_session.add(step)
    db_session.commit()
    
    repo.update_step_execution(step.id, status="FAILED", error="boom")
    
    db_session.refresh(step)
    assert step.status == "FAILED"
    assert step.error == "boom"

def test_fail_step_atomically(db_session):
    repo = SyncWorkflowRepository(db_session)
    execution = WorkflowExecution(workflow_name="test", status="RUNNING", context={})
    db_session.add(execution)
    db_session.commit()
    
    step = StepExecution(workflow_execution_id=execution.id, step_name="my_step", status="RUNNING")
    db_session.add(step)
    db_session.commit()
    
    repo.fail_step_atomically(step.id, execution.id, error="bad thing", new_status="FAILED")
    
    db_session.refresh(step)
    db_session.refresh(execution)
    assert step.status == "FAILED"
    assert step.error == "bad thing"
    assert execution.status == "FAILED"
    assert execution.error == "bad thing"

def test_fail_step_atomically_rollback_on_error(db_session):
    repo = SyncWorkflowRepository(db_session)
    execution = WorkflowExecution(workflow_name="test", status="RUNNING", context={})
    db_session.add(execution)
    db_session.commit()
    
    step = StepExecution(workflow_execution_id=execution.id, step_name="my_step", status="RUNNING")
    db_session.add(step)
    db_session.commit()
    
    # Mocking session.execute to fail on the second call (execution update)
    original_execute = db_session.execute
    call_count = 0
    
    def mocked_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("atomic failure")
        return original_execute(*args, **kwargs)
    
    with patch.object(db_session, 'execute', side_effect=mocked_execute):
        with pytest.raises(Exception, match="atomic failure"):
            repo.fail_step_atomically(step.id, execution.id, error="bad thing")
            
    # Verify rollback by checking that step is still RUNNING
    db_session.refresh(step)
    assert step.status == "RUNNING"
