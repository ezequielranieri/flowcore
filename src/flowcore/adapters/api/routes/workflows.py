# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ....infrastructure.db.session import get_db
from ....infrastructure.repositories.workflow_repository import WorkflowRepository
from ....application.services.workflow_service import WorkflowService
from ...worker.celery_app import celery_app
from ....domain.dsl.exceptions import WorkflowNotFoundError

router = APIRouter()

def get_workflow_service(db: AsyncSession = Depends(get_db)) -> WorkflowService:
    repo = WorkflowRepository(db)
    return WorkflowService(repo, celery_app=celery_app)

@router.post("/{name}")
async def start_workflow(
    name: str, 
    context: Dict[str, Any], 
    service: WorkflowService = Depends(get_workflow_service)
):
    try:
        execution_id = await service.start_workflow(name, context)
        return {"execution_id": execution_id, "status": "PENDING"}
    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/executions/{execution_id}")
async def get_workflow_status(
    execution_id: int, 
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepository(db)
    execution = await repo.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "id": execution.id,
        "workflow_name": execution.workflow_name,
        "status": execution.status,
        "context": execution.context,
        "error": execution.error,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at
    }

