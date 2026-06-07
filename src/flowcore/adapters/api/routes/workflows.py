# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, Any, Optional
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
    version: Optional[str] = None,
    tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
    service: WorkflowService = Depends(get_workflow_service)
):
    try:
        execution_id = await service.start_workflow(name, context, version=version, tenant_id=tenant_id)
        return {"execution_id": execution_id, "status": "PENDING"}
    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/")
async def list_workflows():
    from ....domain.dsl.registry import registry
    workflows = registry.list_workflows()
    return [{"name": w.name, "version": w.version, "description": w.description} for w in workflows]

@router.get("/executions")
async def list_executions(
    limit: int = 20,
    tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepository(db)
    executions = await repo.list_executions(limit, tenant_id=tenant_id)
    return [
        {
            "id": e.id,
            "workflow_name": e.workflow_name,
            "status": e.status,
            "started_at": e.started_at,
            "completed_at": e.completed_at
        }
        for e in executions
    ]

@router.get("/executions/{execution_id}")
async def get_workflow_status(
    execution_id: int, 
    tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepository(db)
    execution = await repo.get_execution(execution_id, tenant_id=tenant_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found or access denied")
    
    return {
        "id": execution.id,
        "workflow_name": execution.workflow_name,
        "status": execution.status,
        "context": execution.context,
        "error": execution.error,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at
    }
