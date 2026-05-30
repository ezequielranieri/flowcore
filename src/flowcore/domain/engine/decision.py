# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import List, Dict, Any, Set
from ..dsl.models import WorkflowDefinition, Step

def evaluate_condition(condition: str, context: Dict[str, Any]) -> bool:
    """
    Evaluates a condition against the context. 
    Currently supports simple key lookup (truthiness of the value).
    """
    if not condition:
        return True
    return bool(context.get(condition, False))

def all_predecessors_completed(step: Step, completed_step_names: Set[str]) -> bool:
    """
    Checks if all steps in 'wait_for' have been completed.
    """
    if not step.wait_for:
        return True
    return all(pre in completed_step_names for pre in step.wait_for)

def determine_next_steps(step: Step, context: Dict[str, Any]) -> List[str]:
    """
    Determines the next steps based on the current step's next_steps and condition.
    """
    if not step.next_steps:
        return []
    
    # If there's a condition and it fails, we don't proceed to next steps
    # (Simplified branch logic: condition applies to all next_steps or none)
    if step.condition and not evaluate_condition(step.condition, context):
        return []
    
    return step.next_steps

