# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import List, Optional
from ..dsl.models import WorkflowDefinition

class SagaOrchestrator:
    def get_compensation_steps(
        self,
        workflow_def: WorkflowDefinition,
        completed_step_names: List[str]
    ) -> List[str]:
        """
        Returns a list of compensation_task names in reverse order
        for the steps that have already completed and have a compensation.
        """
        compensations = []
        # Iterate in reverse order of completion if possible, 
        # but here we follow the workflow definition order in reverse for those completed.
        # A more robust way would be to use the actual completion order from DB if available.
        # For simplicity, we use the reverse order of steps in the workflow def that are in completed_step_names.
        
        for step in reversed(workflow_def.steps):
            if step.name in completed_step_names and step.compensation_task:
                compensations.append(step.compensation_task)
        
        return compensations
    
    def should_compensate(
        self,
        workflow_def: WorkflowDefinition,
        completed_step_names: List[str]
    ) -> bool:
        """
        Returns True if any completed step has a compensation_task.
        """
        for step in workflow_def.steps:
            if step.name in completed_step_names and step.compensation_task:
                return True
        return False
