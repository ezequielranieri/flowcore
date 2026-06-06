# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import Dict, Any, Optional
from ...infrastructure.repositories.workflow_repository import WorkflowRepository
from ...domain.dsl.registry import registry
from ...domain.dsl.exceptions import WorkflowNotFoundError

class WorkflowService:
    def __init__(self, repository: WorkflowRepository, celery_app=None):
        self.repository = repository
        self.celery_app = celery_app

    async def start_workflow(self, workflow_name: str, context: Dict[str, Any], version: Optional[str] = None) -> int:
        """
        Starts a workflow execution.
        1. Validates workflow exists in registry.
        2. Creates execution record in DB.
        3. Enqueues the first steps or the workflow entry point in Celery.
        """
        # Resolve version
        if version is None:
            version = registry.get_latest_version(workflow_name)
            
        # Validate
        workflow_def = registry.get_workflow(workflow_name, version)
        if not workflow_def:
            raise WorkflowNotFoundError(f"{workflow_name} v{version}")

        # Create record
        execution = await self.repository.create_execution(workflow_name, context, workflow_version=version)
        await self.repository.session.commit()

        # Enqueue start
        if self.celery_app:
            # We send a message to start the workflow processing
            # The 'execute_workflow' task is implemented in the adapters layer
            self.celery_app.send_task(
                "flowcore.tasks.execute_workflow",
                args=[execution.id],
                kwargs={}
            )
        
        return execution.id

