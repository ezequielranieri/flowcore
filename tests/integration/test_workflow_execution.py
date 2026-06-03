# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import time
import pytest
from datetime import datetime, timedelta
from flowcore.infrastructure.db.models import WorkflowExecution, StepExecution

def poll_workflow_status(api_client, execution_id, target_status="COMPLETED", timeout=30):
    """Utility to poll for workflow status."""
    start_time = time.time()
    last_status = "UNKNOWN"
    while time.time() - start_time < timeout:
        response = api_client.get(f"/workflows/executions/{execution_id}")
        assert response.status_code == 200
        data = response.json()
        last_status = data["status"]
        if last_status == target_status:
            return data
        if last_status == "FAILED":
            pytest.fail(f"Workflow failed: {data.get('error')}")
        time.sleep(1)
    pytest.fail(f"Workflow did not reach {target_status} within {timeout}s. Current: {last_status}")

def test_simple_workflow_executes_and_completes(api_client, celery_worker, db_session):
    """1. Pruebe que un workflow simple se ejecuta y completa correctamente."""
    # Disparar workflow via API
    response = api_client.post("/workflows/order_process", json={"order_id": "123", "amount": 100.0})
    assert response.status_code == 200
    execution_id = response.json()["execution_id"]

    # Esperar completitud
    final_data = poll_workflow_status(api_client, execution_id)

    # Verificar DB
    steps = db_session.query(StepExecution).filter_by(workflow_execution_id=execution_id).all()
    assert len(steps) == 2
    for step in steps:
        assert step.status == "COMPLETED"

    # Verificar contexto
    assert final_data["context"]["valid"] is True
    assert final_data["context"]["status"] == "paid"

def test_fanout_workflow_completes_correctly(api_client, celery_worker, db_session):
    """2. Pruebe que un workflow con fan-out paralelo completa todos los pasos."""
    response = api_client.post("/workflows/fanout_process", json={"order_id": "456"})
    assert response.status_code == 200
    execution_id = response.json()["execution_id"]

    final_data = poll_workflow_status(api_client, execution_id)
    
    steps = db_session.query(StepExecution).filter_by(workflow_execution_id=execution_id).all()
    assert len(steps) == 3
    step_names = [s.step_name for s in steps]
    assert "validate" in step_names
    assert "notify" in step_names
    assert "inventory" in step_names
    
    for s in steps:
        assert s.status == "COMPLETED"
    
    assert final_data["context"]["email_sent"] is True
    assert final_data["context"]["inventory_updated"] is True

def test_worker_crash_recovery(api_client, db_session, redis_container, postgres_container, workflow_registry):
    """3. Pruebe que los pasos colgados vuelven a PENDING al reiniciar el worker."""
    # 1. Insertar manualmente un StepExecution en RUNNING de hace 20 minutos
    old_time = datetime.utcnow() - timedelta(minutes=20)
    
    execution = WorkflowExecution(workflow_name="order_process", status="RUNNING", context={"order_id": "789"})
    db_session.add(execution)
    db_session.flush()
    
    step = StepExecution(
        workflow_execution_id=execution.id,
        step_name="validate",
        status="RUNNING",
        executed_at=old_time
    )
    db_session.add(step)
    db_session.commit()
    
    step_id = step.id

    # 2. Iniciar el worker (esto disparará el signal worker_init de recuperación)
    from flowcore.adapters.worker.celery_app import celery_app
    import threading
    
    worker = celery_app.Worker(pool='solo', loglevel='info')
    t = threading.Thread(target=worker.start, daemon=True)
    t.start()
    
    try:
        # Dar tiempo a que el signal se ejecute
        time.sleep(3)
        
        # 3. Verificar que el step vuelve a PENDING automáticamente
        db_session.expire_all()
        recovered_step = db_session.get(StepExecution, step_id)
        assert recovered_step.status == "PENDING"
    finally:
        worker.stop()

def test_concurrent_workflows(api_client, celery_worker, db_session):
    """4. Pruebe que múltiples workflows simultáneos no colisionan."""
    ids = []
    num_workflows = 3
    for i in range(num_workflows):
        resp = api_client.post("/workflows/order_process", json={"order_id": f"batch_{i}", "amount": 100.0 * i})
        assert resp.status_code == 200
        ids.append(resp.json()["execution_id"])
    
    for i, eid in enumerate(ids):
        final_data = poll_workflow_status(api_client, eid)
        assert final_data["status"] == "COMPLETED"
        assert final_data["context"]["order_id"] == f"batch_{i}"
        assert final_data["context"]["amount"] == 100.0 * i
