# How-to: Distributed Transactions with Sagas

Distributed systems often require transactions that span multiple services. Flowcore implements the **Saga Pattern** to manage these transactions through compensations.

## What is a Saga?
A Saga is a sequence of local transactions. If one local transaction fails, the Saga executes a series of **compensating transactions** that undo the changes made by the preceding local transactions, ensuring eventual consistency.

## Defining a Saga Step

Use the `@saga_step` decorator to define a task that needs a rollback mechanism.

```python
from flowcore.domain.dsl.primitives import saga_step, task

@saga_step(name="book_flight", compensation="cancel_flight")
def book_flight(ctx: dict):
    print("Booking flight...")
    return {"flight_id": "FL-123"}

@task(name="cancel_flight")
def cancel_flight(ctx: dict):
    flight_id = ctx.get("flight_id")
    print(f"Cancelling flight {flight_id}...")
```

## How Compensations Work

1. **Successful Execution:** If all steps complete, no compensations are run.
2. **Failure:** If a step fails, Flowcore identifies all previously **completed** steps that have a defined `compensation_task`.
3. **Reverse Order:** Compensations are executed in the **reverse order** of completion to restore the system to its original state.
4. **Final Status:** The workflow execution status will be set to `COMPENSATED` if all compensations succeed, or `FAILED` if a compensation fails (manual intervention required).

## Full Example

```python
from flowcore.domain.dsl.primitives import task, saga_step, workflow
from flowcore.domain.dsl.models import Step

@saga_step(name="reserve_inventory", compensation="release_inventory")
def reserve_inventory(ctx: dict):
    return {"inventory_id": "INV-001"}

@task(name="release_inventory")
def release_inventory(ctx: dict):
    print("Inventory released")

@saga_step(name="charge_card", compensation="refund_card")
def charge_card(ctx: dict):
    # Simulate a failure
    raise Exception("Payment gateway unreachable")

@task(name="refund_card")
def refund_card(ctx: dict):
    print("Refund issued")

@workflow(name="payment_saga")
class PaymentSaga:
    steps = [
        Step(name="inventory", task_name="reserve_inventory", next_steps=["payment"]),
        Step(name="payment", task_name="charge_card")
    ]
```

### Expected Output on Failure:
1. `inventory` completes successfully.
2. `payment` fails.
3. Flowcore triggers `release_inventory` (compensation for the only completed saga step).
4. Workflow status: `COMPENSATED`.

## Best Practices
- **Idempotency:** Compensation tasks MUST be idempotent. They might be retried if the worker crashes during rollback.
- **Atomic Operations:** Keep saga steps as small and atomic as possible.
- **Side Effects:** Only use Sagas for operations with side effects that can be undone (e.g., database writes, API calls).
