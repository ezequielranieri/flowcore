import pytest
from flowcore.domain.dsl.registry import registry
from flowcore.domain.dsl.models import TaskDefinition, WorkflowDefinition, Step
from flowcore.infrastructure.repositories.sync_workflow_repository import SyncWorkflowRepository
from sqlalchemy import create_engine
from flowcore.infrastructure.db.session import Base
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_registry_registration():
    def dummy_task(ctx): return {}
    task = TaskDefinition(name="test_task", func=dummy_task)
    registry.register_task(task)
    assert registry.get_task("test_task").name == "test_task"

    workflow = WorkflowDefinition(name="test_workflow")
    registry.register_workflow(workflow)
    assert registry.get_workflow("test_workflow").name == "test_workflow"

def test_repository_crud(db_session):
    repo = SyncWorkflowRepository(db_session)
    # Testing repository logic (creating execution and verifying)
    from flowcore.infrastructure.db.models import WorkflowExecution
    execution = WorkflowExecution(workflow_name="test", status="PENDING", context={})
    db_session.add(execution)
    db_session.commit()
    
    fetched = repo.get_execution(execution.id)
    assert fetched.workflow_name == "test"

def test_wait_for_logic():
    from flowcore.domain.engine.decision import all_predecessors_completed
    step = Step(name="step2", task_name="task", wait_for=["step1"])
    assert not all_predecessors_completed(step, {"step3"})
    assert all_predecessors_completed(step, {"step1"})
