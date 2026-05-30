# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from typing import List, Optional, Dict, Any, Callable
from pydantic import BaseModel, Field, ConfigDict

class TaskDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    max_retries: int = 3
    timeout_seconds: int = 30
    func: Callable

class Step(BaseModel):
    name: str
    task_name: str
    next_steps: List[str] = Field(default_factory=list)
    condition: Optional[str] = None
    wait_for: List[str] = Field(default_factory=list)
    input_mapping: Dict[str, str] = Field(default_factory=dict) # mapping from context to task input

class WorkflowDefinition(BaseModel):
    name: str
    version: str = "1.0.0"
    steps: List[Step] = Field(default_factory=list)
    description: Optional[str] = None

