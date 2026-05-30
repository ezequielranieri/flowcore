# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import Callable, Any, Type, List
from .models import TaskDefinition, WorkflowDefinition, Step
from .registry import registry

def task(name: str, max_retries: int = 3, timeout_seconds: int = 30):
    def decorator(func: Callable) -> Callable:
        task_def = TaskDefinition(
            name=name,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            func=func
        )
        registry.register_task(task_def)
        return func
    return decorator

def workflow(name: str, version: str = "1.0.0"):
    def decorator(cls: Type) -> Type:
        # Expecting the class to have a 'steps' attribute
        steps = getattr(cls, "steps", [])
        description = getattr(cls, "__doc__", None)
        
        workflow_def = WorkflowDefinition(
            name=name,
            version=version,
            steps=steps,
            description=description
        )
        registry.register_workflow(workflow_def)
        return cls
    return decorator

