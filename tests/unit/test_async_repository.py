import pytest
from flowcore.infrastructure.repositories.workflow_repository import WorkflowRepository
from flowcore.infrastructure.db.models import WorkflowExecution, StepExecution, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, UTC

@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with AsyncSessionLocal() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_update_execution_status(async_session):
    repo = WorkflowRepository(async_session)
    execution = await repo.create_execution("wf", {}, tenant_id="default")
    await async_session.commit()
    
    await repo.update_execution_status(execution.id, "COMPLETED")
    await async_session.commit()
    
    fetched = await repo.get_execution(execution.id)
    assert fetched.status == "COMPLETED"

@pytest.mark.asyncio
async def test_update_execution_status_with_completed_at(async_session):
    repo = WorkflowRepository(async_session)
    execution = await repo.create_execution("wf", {})
    await async_session.commit()
    
    now = datetime.now(UTC)
    await repo.update_execution_status(execution.id, "COMPLETED", completed_at=now)
    await async_session.commit()
    
    fetched = await repo.get_execution(execution.id)
    assert fetched.status == "COMPLETED"
    assert fetched.completed_at is not None

@pytest.mark.asyncio
async def test_create_and_get_step_execution(async_session):
    repo = WorkflowRepository(async_session)
    execution = await repo.create_execution("wf", {})
    await async_session.commit()
    
    step = await repo.create_step_execution(execution.id, "step1", {"x": 1})
    await async_session.commit()
    
    assert step.id is not None
    assert step.step_name == "step1"
    assert step.status == "PENDING"

@pytest.mark.asyncio
async def test_get_completed_step_names(async_session):
    repo = WorkflowRepository(async_session)
    execution = await repo.create_execution("wf", {})
    await async_session.commit()
    
    s1 = await repo.create_step_execution(execution.id, "step1", {})
    s2 = await repo.create_step_execution(execution.id, "step2", {})
    await async_session.commit()
    
    await repo.update_step_status(s1.id, "COMPLETED", output_data={"done": True})
    await async_session.commit()
    
    completed = await repo.get_completed_step_names(execution.id)
    assert completed == {"step1"}

@pytest.mark.asyncio
async def test_update_step_status(async_session):
    repo = WorkflowRepository(async_session)
    execution = await repo.create_execution("wf", {})
    await async_session.commit()
    
    step = await repo.create_step_execution(execution.id, "step1", {})
    await async_session.commit()
    
    await repo.update_step_status(step.id, "COMPLETED", output_data={"done": True})
    await async_session.commit()
    
    completed = await repo.get_completed_step_names(execution.id)
    assert "step1" in completed
