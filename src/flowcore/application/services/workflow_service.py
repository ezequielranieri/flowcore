# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import Dict, Any
from ...infrastructure.repositories.workflow_repository import WorkflowRepository
from ...domain.dsl.registry import registry
from ...domain.dsl.exceptions import WorkflowNotFoundError

class WorkflowService:
    def __init__(self, repository: WorkflowRepository, celery_app=None):
        self.repository = repository
        self.celery_app = celery_app

    async def start_workflow(self, workflow_name: str, context: Dict[str, Any]) -> int:
        """
        Starts a workflow execution.
        1. Validates workflow exists in registry.
        2. Creates execution record in DB.
        3. Enqueues the first steps or the workflow entry point in Celery.
        """
        # Validate
        workflow_def = registry.get_workflow(workflow_name)
        if not workflow_def:
            raise WorkflowNotFoundError(workflow_name)

        # Create record
        execution = await self.repository.create_execution(workflow_name, context)
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

