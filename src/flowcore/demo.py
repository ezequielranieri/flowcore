# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from flowcore.domain.dsl.primitives import workflow, task
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
