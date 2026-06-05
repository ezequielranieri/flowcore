# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import pytest
from flowcore.domain.dsl.models import WorkflowDefinition, Step
from flowcore.domain.engine.saga import SagaOrchestrator

def test_saga_orchestrator_gets_compensation_steps():
    workflow_def = WorkflowDefinition(
        name="test_saga",
        steps=[
            Step(name="step1", task_name="task1", compensation_task="comp1"),
            Step(name="step2", task_name="task2", compensation_task="comp2"),
            Step(name="step3", task_name="task3")
        ]
    )
    orchestrator = SagaOrchestrator()
    
    # Only step1 and step2 completed
    completed = ["step1", "step2"]
    compensations = orchestrator.get_compensation_steps(workflow_def, completed)
    
    # Should be in reverse order
    assert compensations == ["comp2", "comp1"]

def test_saga_orchestrator_should_compensate():
    workflow_def = WorkflowDefinition(
        name="test_saga",
        steps=[
            Step(name="step1", task_name="task1", compensation_task="comp1"),
            Step(name="step2", task_name="task2")
        ]
    )
    orchestrator = SagaOrchestrator()
    
    # Case 1: Completed step has compensation
    assert orchestrator.should_compensate(workflow_def, ["step1"]) is True
    
    # Case 2: Completed step has NO compensation
    assert orchestrator.should_compensate(workflow_def, ["step2"]) is False
    
    # Case 3: No steps completed
    assert orchestrator.should_compensate(workflow_def, []) is False

def test_saga_no_compensation_without_saga_steps():
    workflow_def = WorkflowDefinition(
        name="test_saga",
        steps=[
            Step(name="step1", task_name="task1"),
            Step(name="step2", task_name="task2")
        ]
    )
    orchestrator = SagaOrchestrator()
    
    completed = ["step1", "step2"]
    compensations = orchestrator.get_compensation_steps(workflow_def, completed)
    
    assert compensations == []
    assert orchestrator.should_compensate(workflow_def, completed) is False
