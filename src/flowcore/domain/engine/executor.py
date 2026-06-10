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

    def get_initial_steps(self, workflow_def: WorkflowDefinition) -> List[Step]:
        """
        Returns the first steps of the workflow (those without predecessors).
        """
        if not workflow_def.steps:
            return []
        # For now, we assume the first step in the list is the entry point
        # In a real DAG, we'd look for steps with no incoming edges.
        return [workflow_def.steps[0]]

    def execute_step(self, step: Step, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a single step and returns the result.
        """
        from ...domain.dsl.registry import registry
        task_def = registry.get_task(step.task_name)
        result = task_def.func(context)
        return result if isinstance(result, dict) else {}

    def execute_workflow(
        self, 
        workflow_def: WorkflowDefinition, 
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pure domain execution logic (Synchronous/Simulation).
        """
        from loguru import logger
        
        context = initial_context.copy()
        completed_steps: Set[str] = set()
        
        if not workflow_def.steps:
            return context

        queue = deque(self.get_initial_steps(workflow_def))
        
        while queue:
            step = queue.popleft()
            
            if step.name in completed_steps:
                continue

            if not all_predecessors_completed(step, completed_steps):
                continue

            logger.info(f"Executing step: {step.name} (task: {step.task_name})")
            
            # Execute the step
            result = self.execute_step(step, context)
            context.update(result)
            
            completed_steps.add(step.name)
            
            next_step_names = determine_next_steps(step, context)
            for next_name in next_step_names:
                next_step = next((s for s in workflow_def.steps if s.name == next_name), None)
                if next_step and next_step.name not in completed_steps:
                    queue.append(next_step)
        
        return context

