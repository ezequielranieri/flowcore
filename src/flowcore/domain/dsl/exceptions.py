# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

class FlowcoreError(Exception):
    """Base exception for Flowcore."""
    pass

class WorkflowNotFoundError(FlowcoreError):
    """Raised when a workflow definition is not found."""
    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        super().__init__(f"Workflow '{workflow_name}' not found in registry.")

class TaskNotFoundError(FlowcoreError):
    """Raised when a task definition is not found."""
    def __init__(self, task_name: str):
        self.task_name = task_name
        super().__init__(f"Task '{task_name}' not found in registry.")

class StepExecutionError(FlowcoreError):
    """Raised when a step execution fails."""
    pass

class InvalidWorkflowDefinition(FlowcoreError):
    """Raised when a workflow definition is invalid."""
    pass

