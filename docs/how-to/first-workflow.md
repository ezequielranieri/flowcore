# How-to: Create Your First Workflow

This guide will walk you through the process of creating and executing a simple workflow in Flowcore.

## 1. Prerequisites

Ensure you have the project installed and the environment set up:

```bash
# Clone the repository
git clone https://github.com/ezequielranieri/flowcore.git
cd flowcore

# Install dependencies (using uv)
uv sync
```

## 2. Define Your Tasks

Create a new Python file (e.g., `my_workflow.py`) and define some tasks using the `@task` decorator.

```python
from flowcore.domain.dsl.primitives import task

@task(name="hello_task")
def say_hello(ctx: dict):
    name = ctx.get("user_name", "Stranger")
    print(f"Hello, {name}!")
    return {"greeting": f"Welcome, {name}"}

@task(name="log_result")
def log_result(ctx: dict):
    greeting = ctx.get("greeting")
    print(f"Log: {greeting}")
```

## 3. Define the Workflow

Add the workflow definition using the `@workflow` decorator and the `Step` model.

```python
from flowcore.domain.dsl.primitives import workflow
from flowcore.domain.dsl.models import Step

@workflow(name="hello_world_wf", version="1.0.0")
class HelloWorldWorkflow:
    """A simple hello world workflow."""
    steps = [
        Step(name="greet", task_name="hello_task", next_steps=["log"]),
        Step(name="log", task_name="log_result")
    ]
```

## 4. Start the Infrastructure

Before running the workflow, start the Lite stack:

```bash
docker-compose up -d
```

Ensure the worker and API are running:
```bash
docker-compose logs -f
```

## 5. Execute via CLI

You can start the workflow using the Flowcore CLI:

```bash
# Run the workflow with initial context
flowcore run hello_world_wf --context '{"user_name": "Ezequiel"}'
```

Output:
```
Workflow Started: hello_world_wf
Field           Value
Execution ID    1
Status          PENDING
Tenant          default
```

## 6. Check the Result

View the status of your execution:

```bash
flowcore status 1
```

You should see the status change from `RUNNING` to `COMPLETED`. You can also check the logs of the `worker` container to see the print statements.

---

## 7. Next Steps
- Learn how to handle failures with [Sagas](sagas.md).
- Explore [Multi-tenancy](multi-tenancy.md) for isolation.
- Monitor your workflows with [Observability](observability.md).
