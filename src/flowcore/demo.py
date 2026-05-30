# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from flowcore.domain.dsl.primitives import workflow, task
from flowcore.domain.dsl.models import Step

@task(name="validate_order", max_retries=3)
def validate_order(order_id: int):
    print(f"Validating order {order_id}")
    return {"valid": True}

@task(name="process_payment")
def process_payment(amount: float):
    print(f"Processing payment of {amount}")
    return {"status": "paid"}

@workflow(name="order_process", version="1.0.0")
class OrderWorkflow:
    """Proceso de validación y pago de pedidos."""
    steps = [
        Step(name="validate", task_name="validate_order", next_steps=["pay"]),
        Step(name="pay", task_name="process_payment")
    ]

