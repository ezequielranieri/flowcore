# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import Dict, List, Optional
from .models import WorkflowDefinition, TaskDefinition
from .exceptions import WorkflowNotFoundError, TaskNotFoundError

class Registry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Registry, cls).__new__(cls)
            # {workflow_name: {version: WorkflowDefinition}}
            cls._instance.workflows: Dict[str, Dict[str, WorkflowDefinition]] = {}
            cls._instance.tasks: Dict[str, TaskDefinition] = {}
        return cls._instance

    def register_workflow(self, workflow: WorkflowDefinition):
        if workflow.name not in self.workflows:
            self.workflows[workflow.name] = {}
        self.workflows[workflow.name][workflow.version] = workflow

    def register_task(self, task: TaskDefinition):
        self.tasks[task.name] = task

    def get_workflow(self, name: str, version: Optional[str] = None) -> WorkflowDefinition:
        if name not in self.workflows:
            raise WorkflowNotFoundError(name)
        
        versions = self.workflows[name]
        if version is None:
            # Get latest version (last registered)
            latest_version = list(versions.keys())[-1]
            return versions[latest_version]
        
        if version not in versions:
            raise WorkflowNotFoundError(f"{name} (version {version})")
        
        return versions[version]

    def get_task(self, name: str) -> TaskDefinition:
        if name not in self.tasks:
            raise TaskNotFoundError(name)
        return self.tasks[name]

    def list_workflows(self) -> List[WorkflowDefinition]:
        # Return all versions of all workflows
        all_workflows = []
        for name_versions in self.workflows.values():
            all_workflows.extend(name_versions.values())
        return all_workflows

    def get_latest_version(self, name: str) -> str:
        if name not in self.workflows:
            raise WorkflowNotFoundError(name)
        return list(self.workflows[name].keys())[-1]

    def list_tasks(self) -> List[TaskDefinition]:
        return list(self.tasks.values())

# Global registry instance
registry = Registry()
