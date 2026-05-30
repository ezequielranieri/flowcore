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
        # Using options(selectinload(...)) with sync session
        result = self.session.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.id == execution_id)
            .options(selectinload(WorkflowExecution.steps))
        )
        return result.scalar_one_or_none()

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

