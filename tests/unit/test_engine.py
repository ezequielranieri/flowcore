import pytest
from flowcore.domain.engine.executor import WorkflowEngine
from flowcore.domain.dsl.models import WorkflowDefinition, Step, TaskDefinition
from flowcore.domain.dsl.registry import registry

def test_engine_execution_and_context():
    def task_a(ctx): return {"key_a": "val_a"}
    def task_b(ctx): return {"key_b": "val_b"}
    
    registry.register_task(TaskDefinition(name="task_a", func=task_a))
    registry.register_task(TaskDefinition(name="task_b", func=task_b))
    
    workflow = WorkflowDefinition(
        name="wf",
        steps=[
            Step(name="step_a", task_name="task_a", next_steps=["step_b"]),
            Step(name="step_b", task_name="task_b")
        ]
    )
    
    engine = WorkflowEngine()
    final_context = engine.execute_workflow(workflow, {})
    assert final_context == {"key_a": "val_a", "key_b": "val_b"}

def test_fan_out():
    def task_a(ctx): return {"a": 1}
    def task_b(ctx): return {"b": 2}
    
    registry.register_task(TaskDefinition(name="task_a", func=task_a))
    registry.register_task(TaskDefinition(name="task_b", func=task_b))
    
    workflow = WorkflowDefinition(
        name="wf_fanout",
        steps=[
            Step(name="a", task_name="task_a", next_steps=["b", "c"]),
            Step(name="b", task_name="task_b"),
            Step(name="c", task_name="task_b")
        ]
    )
    
    engine = WorkflowEngine()
    final_context = engine.execute_workflow(workflow, {})
    assert "a" in final_context
    assert "b" in final_context

def test_condition():
    def task_a(ctx): return {"should_run": True}
    def task_b(ctx): return {"b": 1}
    
    registry.register_task(TaskDefinition(name="task_a", func=task_a))
    registry.register_task(TaskDefinition(name="task_b", func=task_b))
    
    workflow = WorkflowDefinition(
        name="wf_cond",
        steps=[
            Step(name="a", task_name="task_a", next_steps=["b"]),
            Step(name="b", task_name="task_b", condition="should_run")
        ]
    )
    
    engine = WorkflowEngine()
    final_context = engine.execute_workflow(workflow, {})
    assert final_context["b"] == 1
