# DSL Reference

Flowcore uses a Python-based DSL to define tasks and workflows. This document provides an exhaustive reference of all DSL components.

## Decorators

### `@task`
The basic building block of Flowcore. It registers a Python function as a task that can be executed by the worker.

**Location:** `src/flowcore/domain/dsl/primitives.py`

**Parameters:**
- `name` (str): Unique name of the task in the registry.
- `max_retries` (int, default=3): Number of times to retry the task if it fails.
- `timeout_seconds` (int, default=30): Maximum time the task is allowed to run before being killed.

**Example:**
```python
from flowcore.domain.dsl.primitives import task

@task(name="process_data", max_retries=5, timeout_seconds=60)
def process_data(ctx: dict):
    data = ctx.get("input")
    # logic here
    return {"result": "processed"}
```

**Retry mechanism:**
Flowcore implements retries with exponential backoff. If a task fails, it will be rescheduled for execution according to its `max_retries` configuration.

---

### `@saga_step`
Specialized decorator for tasks that participate in a Saga pattern. It requires a compensation task.

**Parameters:**
- `name` (str): Unique name of the task.
- `compensation` (str): Name of the task to execute if the workflow fails later and this step needs to be rolled back.
- `max_retries` (int, default=3): Standard retry configuration.

**Compensation Logic:**
Compensations are executed in **reverse order** of completion. If Step A, B, and C completed, and Step D fails, Flowcore will run compensations for C, then B, then A (if defined).

**Example:**
```python
@saga_step(name="reserve_funds", compensation="release_funds")
def reserve_funds(ctx: dict):
    # logic to reserve funds
    return {"funds_reserved": True}

@task(name="release_funds")
def release_funds(ctx: dict):
    # logic to rollback fund reservation
    return {"funds_released": True}
```

---

### `@workflow`
Registers a class as a workflow definition.

**Parameters:**
- `name` (str): Unique name of the workflow.
- `version` (str, default="1.0.0"): Version of the workflow.

**Registration:**
When the module containing the `@workflow` decorated class is imported, the workflow is automatically registered in the `registry`.

**Example:**
```python
@workflow(name="onboarding", version="1.1.0")
class OnboardingWorkflow:
    """User onboarding process."""
    steps = [
        Step(name="welcome", task_name="send_welcome_email"),
        # ...
    ]
```

---

## Models

### Step
Defines an instance of a task within a workflow and its execution flow.

**Fields:**
- `name` (str): Unique name of the step within the workflow.
- `task_name` (str): The name of the task (registered via `@task` or `@saga_step`) to execute.
- `next_steps` (List[str]): List of step names to trigger after this one completes.
- `condition` (Optional[str]): A Python expression (evaluated against the context) to determine if this step should run.
- `wait_for` (List[str]): List of step names that must complete before this step starts (Barrier/Join).
- `input_mapping` (Dict[str, str]): Mapping from context keys to task arguments.
- `compensation_task` (Optional[str]): Name of the compensation task (usually populated automatically by `@saga_step`).

**Examples:**

**Linear Flow:**
```python
Step(name="step1", task_name="task1", next_steps=["step2"])
```

**Fan-out (Parallel):**
```python
Step(name="start", task_name="init", next_steps=["branch_a", "branch_b"])
```

**Join / Barrier:**
```python
Step(name="final", task_name="merge", wait_for=["branch_a", "branch_b"])
```

---

### WorkflowDefinition
The top-level model representing a registered workflow.

**Fields:**
- `name` (str): Unique identifier.
- `version` (str): Semantic versioning.
- `steps` (List[Step]): List of steps that form the DAG.
- `description` (str): Optional docstring from the workflow class.

**Persistence:**
Workflow definitions are registered in memory via the `registry` and can be queried via the API or CLI. Execution state is persisted in the `workflow_executions` table in PostgreSQL.
