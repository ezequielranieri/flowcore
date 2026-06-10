# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>
"""
Example 3: Workflow Versioning in Action

This example demonstrates Flowcore's native support for workflow versioning.
In real-world systems, you often need to update a business process 
without breaking executions that are already in progress.

Scenario:
- v1.0.0: Simple flow (Validate -> Process -> Notify)
- v2.0.0: Improved flow with an extra enrichment step (Validate -> ENRICH -> Process -> Notify)

Features shown:
- Versioned @workflow definitions.
- Running multiple versions of the same workflow name simultaneously.
"""

from flowcore.domain.dsl.primitives import task, workflow
from flowcore.domain.dsl.models import Step
from flowcore.domain.engine.executor import WorkflowEngine
from flowcore.domain.dsl.registry import registry

# 1. Define Common Tasks
@task(name="validate")
def validate(ctx: dict):
    print(f" [Step] Validating input for {ctx.get('item')}...")
    return {"valid": True}

@task(name="process")
def process(ctx: dict):
    print(f" [Step] Processing {ctx.get('item')}...")
    return {"processed": True}

@task(name="notify")
def notify(ctx: dict):
    print(f" [Step] Notifying user about {ctx.get('item')}.")
    return {"notified": True}

# 2. Define New Task for V2
@task(name="enrich_data")
def enrich_data(ctx: dict):
    print(f" [Step] ENRICHING data with external metadata for {ctx.get('item')}...")
    return {"metadata": "v2-premium-data"}

# 3. Define Workflow Version 1.0.0
@workflow(name="deployment_flow", version="1.0.0")
class DeploymentFlowV1:
    """Standard deployment flow."""
    steps = [
        Step(name="v", task_name="validate", next_steps=["p"]),
        Step(name="p", task_name="process", next_steps=["n"]),
        Step(name="n", task_name="notify"),
    ]

# 4. Define Workflow Version 2.0.0
@workflow(name="deployment_flow", version="2.0.0")
class DeploymentFlowV2:
    """Improved deployment flow with data enrichment."""
    steps = [
        Step(name="v", task_name="validate", next_steps=["e"]),
        Step(name="e", task_name="enrich_data", next_steps=["p"]),
        Step(name="p", task_name="process", next_steps=["n"]),
        Step(name="n", task_name="notify"),
    ]

def run_version(version: str, item_name: str):
    print(f"\n--- Running 'deployment_flow' version {version} for {item_name} ---")
    wf = registry.get_workflow("deployment_flow", version)
    engine = WorkflowEngine()
    final_context = engine.execute_workflow(wf, {"item": item_name})
    print(f"--- Finished v{version}. Final Context: {final_context} ---")

if __name__ == "__main__":
    # Simulate an "old" execution still running v1.0.0
    run_version("1.0.0", "Legacy Order #101")
    
    # Simulate a "new" execution using v2.0.0
    run_version("2.0.0", "New Premium Order #202")

"""
Output esperado:

--- Running 'deployment_flow' version 1.0.0 for Legacy Order #101 ---
Executing step: v (task: validate)
 [Step] Validating input for Legacy Order #101...
Executing step: p (task: process)
 [Step] Processing Legacy Order #101...
Executing step: n (task: notify)
 [Step] Notifying user about Legacy Order #101.
--- Finished v1.0.0. Final Context: {'item': 'Legacy Order #101', 'valid': True, 'processed': True, 'notified': True} ---

--- Running 'deployment_flow' version 2.0.0 for New Premium Order #202 ---
Executing step: v (task: validate)
 [Step] Validating input for New Premium Order #202...
Executing step: e (task: enrich_data)
 [Step] ENRICHING data with external metadata for New Premium Order #202...
Executing step: p (task: process)
 [Step] Processing New Premium Order #202...
Executing step: n (task: notify)
 [Step] Notifying user about New Premium Order #202.
--- Finished v2.0.0. Final Context: {'item': 'New Premium Order #202', 'valid': True, 'metadata': 'v2-premium-data', 'processed': True, 'notified': True} ---
"""
