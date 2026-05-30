# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import math
import time
from collections import deque
from typing import Dict, Any, List, Set, Optional
from datetime import datetime, timedelta

from ..dsl.models import WorkflowDefinition, Step
from .decision import determine_next_steps, all_predecessors_completed

class WorkflowEngine:
    @staticmethod
    def calculate_backoff(retry_count: int) -> int:
        """
        Calculates exponential backoff capped at 300 seconds.
        """
        delay = min(300, math.pow(2, retry_count))
        return int(delay)

    def execute_workflow(
        self, 
        workflow_def: WorkflowDefinition, 
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pure domain execution logic.
        """
        from loguru import logger
        from ...domain.dsl.registry import registry
        
        context = initial_context.copy()
        completed_steps: Set[str] = set()
        
        if not workflow_def.steps:
            return context

        queue = deque([workflow_def.steps[0]])
        
        while queue:
            step = queue.popleft()
            
            if not all_predecessors_completed(step, completed_steps):
                continue

            logger.info(f"Executing step: {step.name} (task: {step.task_name})")
            
            # Execute the task
            task_def = registry.get_task(step.task_name)
            result = task_def.func(context)
            if isinstance(result, dict):
                context.update(result)
            
            completed_steps.add(step.name)
            
            next_step_names = determine_next_steps(step, context)
            for next_name in next_step_names:
                next_step = next((s for s in workflow_def.steps if s.name == next_name), None)
                if next_step and next_step.name not in completed_steps:
                    queue.append(next_step)
        
        return context

