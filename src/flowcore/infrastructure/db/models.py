# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .session import Base

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(100), default="default", index=True)
    workflow_name: Mapped[str] = mapped_column(String(255))
    workflow_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    current_step_name: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED, COMPENSATING, COMPENSATED
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    steps: Mapped[list["StepExecution"]] = relationship(back_populates="workflow_execution", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, name={self.workflow_name}, status={self.status})>"

class StepExecution(Base):
    __tablename__ = "step_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_execution_id: Mapped[int] = mapped_column(ForeignKey("workflow_executions.id"))
    step_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    workflow_execution: Mapped["WorkflowExecution"] = relationship(back_populates="steps")

    def __repr__(self) -> str:
        return f"<StepExecution(id={self.id}, step={self.step_name}, status={self.status})>"

