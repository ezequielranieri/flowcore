import pytest
from src.flowcore.domain.engine.dag import WorkflowDAG
from src.flowcore.domain.dsl.models import WorkflowDefinition, Step

def test_dag_construction_and_terminal_nodes():
    wf = WorkflowDefinition(
        name="test_wf",
        steps=[
            Step(name="a", task_name="t", next_steps=["b", "c"]),
            Step(name="b", task_name="t", next_steps=["d"]),
            Step(name="c", task_name="t", next_steps=["d"]),
            Step(name="d", task_name="t")
        ]
    )
    dag = WorkflowDAG(wf)
    assert dag.validate() is True
    assert set(dag.get_terminal_nodes()) == {"d"}

def test_dag_validation_cycle():
    wf = WorkflowDefinition(
        name="cycle_wf",
        steps=[
            Step(name="a", task_name="t", next_steps=["b"]),
            Step(name="b", task_name="t", next_steps=["a"])
        ]
    )
    dag = WorkflowDAG(wf)
    assert dag.validate() is False

def test_workflow_completion():
    wf = WorkflowDefinition(
        name="test_wf",
        steps=[
            Step(name="a", task_name="t", next_steps=["b", "c"]),
            Step(name="b", task_name="t"),
            Step(name="c", task_name="t")
        ]
    )
    dag = WorkflowDAG(wf)
    
    # Not complete yet
    assert dag.is_workflow_complete({"a", "b"}) is False
    assert dag.is_workflow_complete({"b", "c"}) is True # Terminal nodes completed
    assert dag.is_workflow_complete({"a", "b", "c"}) is True

def test_complex_completion():
    # a -> b -> d
    #   -> c -> e
    wf = WorkflowDefinition(
        name="complex",
        steps=[
            Step(name="a", task_name="t", next_steps=["b", "c"]),
            Step(name="b", task_name="t", next_steps=["d"]),
            Step(name="c", task_name="t", next_steps=["e"]),
            Step(name="d", task_name="t"),
            Step(name="e", task_name="t")
        ]
    )
    dag = WorkflowDAG(wf)
    assert dag.is_workflow_complete({"d"}) is False
    assert dag.is_workflow_complete({"d", "e"}) is True
