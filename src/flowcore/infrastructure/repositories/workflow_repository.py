# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ...infrastructure.db.models import WorkflowExecution, StepExecution

class WorkflowRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_execution(self, workflow_name: str, context: Dict[str, Any]) -> WorkflowExecution:
        execution = WorkflowExecution(
            workflow_name=workflow_name,
            context=context,
            status="PENDING"
        )
        self.session.add(execution)
        await self.session.flush()
        return execution

    async def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        result = await self.session.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.id == execution_id)
            .options(selectinload(WorkflowExecution.steps))
        )
        return result.scalar_one_or_none()

    async def update_execution_status(self, execution_id: int, status: str, error: Optional[str] = None, completed_at: Optional[datetime] = None):
        values = {"status": status, "error": error}
        if completed_at:
            values["completed_at"] = completed_at
        
        await self.session.execute(
            update(WorkflowExecution)
            .where(WorkflowExecution.id == execution_id)
            .values(**values)
        )

    async def create_step_execution(
        self, 
        execution_id: int, 
        step_name: str, 
        input_data: Dict[str, Any]
    ) -> StepExecution:
        step = StepExecution(
            workflow_execution_id=execution_id,
            step_name=step_name,
            input_data=input_data,
            status="PENDING"
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def get_completed_step_names(self, execution_id: int) -> Set[str]:
        result = await self.session.execute(
            select(StepExecution.step_name)
            .where(StepExecution.workflow_execution_id == execution_id)
            .where(StepExecution.status == "COMPLETED")
        )
        return set(result.scalars().all())

    async def list_executions(self, limit: int = 20) -> List[WorkflowExecution]:
        result = await self.session.execute(
            select(WorkflowExecution)
            .order_by(WorkflowExecution.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_step_status(
        self, 
        step_id: int, 
        status: str, 
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        await self.session.execute(
            update(StepExecution)
            .where(StepExecution.id == step_id)
            .values(status=status, output_data=output_data, error=error)
        )

