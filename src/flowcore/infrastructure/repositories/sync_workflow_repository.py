# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload
from ...infrastructure.db.models import WorkflowExecution, StepExecution

class SyncWorkflowRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_stuck_steps(self, timeout_minutes: int) -> List[StepExecution]:
        from datetime import datetime, timedelta
        
        limit_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        result = self.session.execute(
            select(StepExecution)
            .where(StepExecution.status == "RUNNING")
            .where(StepExecution.executed_at < limit_time) # Assuming executed_at is the last update time, based on schema
        )
        return list(result.scalars().all())

    def reset_step_status(self, step_id: int):
        self.session.execute(
            update(StepExecution)
            .where(StepExecution.id == step_id)
            .values(status="PENDING", error="Reset by recovery mechanism")
        )
        self.session.commit()

    def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        return self.session.get(
            WorkflowExecution, 
            execution_id, 
            options=[selectinload(WorkflowExecution.steps)]
        )

    def update_execution_status(self, execution_id: int, status: str, error: Optional[str] = None, completed_at: Optional[datetime] = None):
        values = {"status": status, "error": error}
        if completed_at:
            values["completed_at"] = completed_at
        
        self.session.execute(
            update(WorkflowExecution)
            .where(WorkflowExecution.id == execution_id)
            .values(**values)
        )
        self.session.commit()

    def update_execution_context(self, execution_id: int, context: Dict[str, Any]):
        self.session.execute(
            update(WorkflowExecution)
            .where(WorkflowExecution.id == execution_id)
            .values(context=context, updated_at=datetime.utcnow())
        )
        self.session.commit()

    def get_step_execution(self, execution_id: int, step_name: str) -> Optional[StepExecution]:
        result = self.session.execute(
            select(StepExecution)
            .where(StepExecution.workflow_execution_id == execution_id)
            .where(StepExecution.step_name == step_name)
        )
        return result.scalar_one_or_none()

    def create_step_execution(self, execution_id: int, step_name: str, input_data: Dict[str, Any]) -> StepExecution:
        step_exec = StepExecution(
            workflow_execution_id=execution_id,
            step_name=step_name,
            input_data=input_data,
            status="PENDING"
        )
        self.session.add(step_exec)
        self.session.commit()
        self.session.refresh(step_exec)
        return step_exec

    def update_step_execution(
        self, 
        step_id: int, 
        status: str, 
        output_data: Optional[Dict[str, Any]] = None, 
        error: Optional[str] = None
    ):
        values = {"status": status, "error": error}
        if output_data is not None:
            values["output_data"] = output_data
        if status == "COMPLETED":
            values["completed_at"] = datetime.utcnow()
        
        self.session.execute(
            update(StepExecution)
            .where(StepExecution.id == step_id)
            .values(**values)
        )
        self.session.commit()

    def get_completed_step_names(self, execution_id: int) -> Set[str]:
        result = self.session.execute(
            select(StepExecution.step_name)
            .where(StepExecution.workflow_execution_id == execution_id)
            .where(StepExecution.status == "COMPLETED")
        )
        return {row[0] for row in result.all()}

