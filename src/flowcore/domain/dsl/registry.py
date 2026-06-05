# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import Dict
from .models import WorkflowDefinition, TaskDefinition
from .exceptions import WorkflowNotFoundError, TaskNotFoundError

class Registry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Registry, cls).__new__(cls)
            cls._instance.workflows: Dict[str, WorkflowDefinition] = {}
            cls._instance.tasks: Dict[str, TaskDefinition] = {}
        return cls._instance

    def register_workflow(self, workflow: WorkflowDefinition):
        self.workflows[workflow.name] = workflow

    def register_task(self, task: TaskDefinition):
        self.tasks[task.name] = task

    def get_workflow(self, name: str) -> WorkflowDefinition:
        if name not in self.workflows:
            raise WorkflowNotFoundError(name)
        return self.workflows[name]

    def get_task(self, name: str) -> TaskDefinition:
        if name not in self.tasks:
            raise TaskNotFoundError(name)
        return self.tasks[name]

    def list_workflows(self):
        return list(self.workflows.values())

    def list_tasks(self):
        return list(self.tasks.values())

# Global registry instance
registry = Registry()

