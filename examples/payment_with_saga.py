# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>
"""
Example 1: Payment Pipeline with Saga Pattern

This example demonstrates how Flowcore handles distributed transactions 
using the Saga pattern. If a step fails, all previously completed 
steps with defined compensations are rolled back automatically in reverse order.

Features shown:
- @saga_step: Defines a task with its compensation logic.
- Automatic Rollback: Reverse execution of compensations on failure.
"""

from flowcore.domain.dsl.primitives import task, saga_step, workflow
from flowcore.domain.dsl.models import Step
from flowcore.domain.dsl.registry import registry
from flowcore.domain.engine.saga import SagaOrchestrator

# 1. Define Tasks
@task(name="validate_payment")
def validate_payment(ctx: dict):
    print(" [Step] Validating payment amount...")
    amount = ctx.get("amount", 0)
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return {"validated": True}

@saga_step(name="reserve_funds", compensation="release_funds")
def reserve_funds(ctx: dict):
    print(f" [Saga Step] Reserving ${ctx['amount']} from user account...")
    return {"funds_reserved": True}

@task(name="release_funds")
def release_funds(ctx: dict):
    print(" [Compensation] Releasing reserved funds...")
    return {"funds_released": True}

@saga_step(name="reserve_inventory", compensation="release_inventory")
def reserve_inventory(ctx: dict):
    print(f" [Saga Step] Reserving item {ctx['item_id']} in inventory...")
    return {"inventory_reserved": True}

@task(name="release_inventory")
def release_inventory(ctx: dict):
    print(" [Compensation] Releasing inventory reservation...")
    return {"inventory_released": True}

@task(name="process_payment")
def process_payment(ctx: dict):
    amount = ctx.get("amount", 0)
    print(f" [Step] Processing actual payment of ${amount}...")
    if amount > 1000:
        print(" [!] Payment gateway rejected: High amount detected.")
        raise Exception("Payment gateway error: Transaction limit exceeded")
    return {"payment_processed": True}

@task(name="send_confirmation")
def send_confirmation(ctx: dict):
    print(" [Step] Sending confirmation email to user.")
    return {"confirmed": True}

# 2. Define Workflow
@workflow(name="payment_saga", version="1.0.0")
class PaymentSagaWorkflow:
    """A payment pipeline with inventory and funds reservation."""
    steps = [
        Step(name="validate", task_name="validate_payment", next_steps=["reserve_funds"]),
        Step(name="reserve_funds", task_name="reserve_funds", 
             next_steps=["reserve_inventory"], compensation_task="release_funds"),
        Step(name="reserve_inventory", task_name="reserve_inventory", 
             next_steps=["process"], compensation_task="release_inventory"),
        Step(name="process", task_name="process_payment", next_steps=["notify"]),
        Step(name="notify", task_name="send_confirmation"),
    ]

# 3. Execution Simulation logic (Simulating the Worker behavior)
# NOTE: This is a standalone simulation for demonstration purposes.
# In production, the WorkflowEngine and Celery handle execution,
# state persistence, and automatic saga compensation automatically.
# See the README for the full distributed setup.
def run_example(amount: int):
    print(f"\n--- Running Payment Workflow with amount: ${amount} ---")
    wf = registry.get_workflow("payment_saga", "1.0.0")
    context = {"amount": amount, "item_id": "SKU-123"}
    completed = []
    
    try:
        for step in wf.steps:
            task_def = registry.get_task(step.task_name)
            result = task_def.func(context)
            context.update(result)
            completed.append(step.name)
            
        print("--- Workflow Completed Successfully! ---")
    except Exception as e:
        print(f"--- Workflow Failed: {e} ---")
        print("Starting Saga Compensation Sequence...")
        
        saga = SagaOrchestrator()
        compensations = saga.get_compensation_steps(wf, completed)
        
        for comp_name in compensations:
            comp_task = registry.get_task(comp_name)
            comp_task.func(context)
            
        print("--- All compensations completed. System is consistent. ---")

if __name__ == "__main__":
    # Case 1: Success
    run_example(amount=500)
    
    # Case 2: Failure (High amount triggers compensation)
    run_example(amount=1500)

"""
Output esperado:

--- Running Payment Workflow with amount: $500 ---
 [Step] Validating payment amount...
 [Saga Step] Reserving $500 from user account...
 [Saga Step] Reserving item SKU-123 in inventory...
 [Step] Processing actual payment of $500...
 [Step] Sending confirmation email to user.
--- Workflow Completed Successfully! ---

--- Running Payment Workflow with amount: $1500 ---
 [Step] Validating payment amount...
 [Saga Step] Reserving $1500 from user account...
 [Saga Step] Reserving item SKU-123 in inventory...
 [Step] Processing actual payment of $1500...
 [!] Payment gateway rejected: High amount detected.
--- Workflow Failed: Payment gateway error: Transaction limit exceeded ---
Starting Saga Compensation Sequence...
 [Compensation] Releasing inventory reservation...
 [Compensation] Releasing reserved funds...
--- All compensations completed. System is consistent. ---
"""
