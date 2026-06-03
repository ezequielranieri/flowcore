from flowcore.domain.engine.decision import evaluate_condition, all_predecessors_completed, determine_next_steps
from flowcore.domain.dsl.models import Step

def test_evaluate_condition():
    assert evaluate_condition("key", {"key": True})
    assert not evaluate_condition("key", {"key": False})
    assert not evaluate_condition("nonexistent", {})

def test_all_predecessors():
    step = Step(name="s", task_name="t", wait_for=["p1", "p2"])
    assert not all_predecessors_completed(step, {"p1"})
    assert all_predecessors_completed(step, {"p1", "p2"})

def test_determine_next_steps():
    step = Step(name="s", task_name="t", next_steps=["n1"], condition="c")
    assert determine_next_steps(step, {"c": True}) == ["n1"]
    assert determine_next_steps(step, {"c": False}) == []
