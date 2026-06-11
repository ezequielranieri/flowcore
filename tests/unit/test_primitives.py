# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import pytest
from flowcore.domain.dsl.primitives import task, saga_step, workflow
from flowcore.domain.dsl.registry import registry
from flowcore.domain.dsl.models import Step

def test_task_decorator_registers_in_registry():
    @task(name="test_primitive_task", max_retries=5, timeout_seconds=45)
    def my_func(ctx):
        return {"ok": True}
    
    task_def = registry.get_task("test_primitive_task")
    assert task_def is not None
    assert task_def.name == "test_primitive_task"
    assert task_def.max_retries == 5
    assert task_def.timeout_seconds == 45
    assert task_def.func == my_func

def test_task_decorator_preserves_function():
    @task(name="preservation_task")
    def my_func(a, b):
        return a + b
    
    assert my_func(1, 2) == 3
    assert callable(my_func)

def test_saga_step_decorator_registers_with_compensation():
    @saga_step(name="saga_prim_task", compensation="my_comp")
    def my_func(ctx):
        pass
    
    task_def = registry.get_task("saga_prim_task")
    assert task_def.compensation_task == "my_comp"

def test_workflow_decorator_registers_workflow():
    @workflow(name="prim_workflow", version="2.0.0")
    class MyWorkflow:
        steps = [Step(name="s1", task_name="t1")]
    
    wf_def = registry.get_workflow("prim_workflow", "2.0.0")
    assert wf_def is not None
    assert wf_def.name == "prim_workflow"
    assert wf_def.version == "2.0.0"
    assert len(wf_def.steps) == 1

def test_workflow_decorator_uses_docstring_as_description():
    @workflow(name="desc_workflow")
    class MyWorkflow:
        """This is a test description."""
        steps = []
    
    wf_def = registry.get_workflow("desc_workflow")
    assert wf_def.description == "This is a test description."
