# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from flowcore.domain.dsl.primitives import workflow, task, saga_step
from flowcore.domain.dsl.models import Step

@task(name="validate_order", max_retries=3)
def validate_order(ctx: dict):
    order_id = ctx.get("order_id")
    print(f"Validating order {order_id}")
    return {"valid": True}

@task(name="process_payment")
def process_payment(ctx: dict):
    amount = ctx.get("amount")
    print(f"Processing payment of {amount}")
    return {"status": "paid"}

@task(name="send_email")
def send_email(ctx: dict):
    print("Sending confirmation email")
    return {"email_sent": True}

@task(name="update_inventory")
def update_inventory(ctx: dict):
    print("Updating inventory")
    return {"inventory_updated": True}

@workflow(name="order_process", version="1.0.0")
class OrderWorkflow:
    """Proceso de validación y pago de pedidos."""
    steps = [
        Step(name="validate", task_name="validate_order", next_steps=["pay"]),
        Step(name="pay", task_name="process_payment")
    ]

@workflow(name="fanout_process", version="1.0.0")
class FanoutWorkflow:
    """Proceso con fan-out paralelo."""
    steps = [
        Step(name="validate", task_name="validate_order", next_steps=["notify", "inventory"]),
        Step(name="notify", task_name="send_email"),
        Step(name="inventory", task_name="update_inventory")
    ]

# Saga Example
@saga_step(name="reserve_inventory", compensation="release_inventory")
def reserve_inventory(ctx: dict):
    print(f"Reserving inventory for order {ctx.get('order_id')}")
    return {"inventory_reserved": True}

@task(name="release_inventory")
def release_inventory(ctx: dict):
    print(f"Releasing inventory for order {ctx.get('order_id')}")
    return {"inventory_released": True}

@saga_step(name="process_payment_saga", compensation="refund_payment")
def process_payment_saga(ctx: dict):
    print(f"Processing payment for order {ctx.get('order_id')}")
    return {"payment_processed": True}

@task(name="refund_payment")
def refund_payment(ctx: dict):
    print(f"Refunding payment for order {ctx.get('order_id')}")
    return {"payment_refunded": True}

@task(name="fail_intentionally")
def fail_intentionally(ctx: dict):
    raise Exception("Intentional failure to trigger saga compensation")

@workflow(name="saga_order_process", version="1.0.0")
class SagaOrderWorkflow:
    """Workflow con saga para demostrar compensaciones automáticas."""
    steps = [
        Step(name="reserve", task_name="reserve_inventory", 
             next_steps=["pay"], compensation_task="release_inventory"),
        Step(name="pay", task_name="process_payment_saga",
             next_steps=["fail"], compensation_task="refund_payment"),
        Step(name="fail", task_name="fail_intentionally"),
    ]
