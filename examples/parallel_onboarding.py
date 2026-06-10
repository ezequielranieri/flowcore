# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>
"""
Example 2: Parallel User Onboarding (Fan-out & Join/Barrier)

This example demonstrates how Flowcore handles parallel execution using 
the DAG (Directed Acyclic Graph) engine. Multiple tasks run in parallel 
(Fan-out), and a final task waits for all of them to complete (Join/Barrier).

Diagram:
  create_account
       |
  +---------+-----------+
  |         |           |
  setup  welcome    profile
  perms   email
  |         |           |
  +---------+-----------+
       |
  activate_account

Features shown:
- Fan-out: One step triggering multiple next_steps.
- Join/Barrier: Using 'wait_for' to synchronize multiple parallel branches.
"""

import time
from flowcore.domain.dsl.primitives import task, workflow
from flowcore.domain.dsl.models import Step
from flowcore.domain.engine.executor import WorkflowEngine
from flowcore.domain.dsl.registry import registry

# 1. Define Tasks
@task(name="create_account")
def create_account(ctx: dict):
    print(" [Step] Creating user account in database...")
    return {"user_id": 42, "username": "ezranieri"}

@task(name="setup_permissions")
def setup_permissions(ctx: dict):
    print(" [Step] Setting up default permissions (Parallel)...")
    time.sleep(0.1)  # Simulate some work
    return {"perms_ok": True}

@task(name="send_welcome_email")
def send_welcome_email(ctx: dict):
    print(" [Step] Sending welcome email (Parallel)...")
    time.sleep(0.2)  # Simulate some work
    return {"email_sent": True}

@task(name="create_user_profile")
def create_user_profile(ctx: dict):
    print(" [Step] Initializing user profile (Parallel)...")
    time.sleep(0.15) # Simulate some work
    return {"profile_created": True}

@task(name="activate_account")
def activate_account(ctx: dict):
    print(" [Step] All parallel tasks finished. ACTIVATING ACCOUNT.")
    return {"status": "ACTIVE"}

# 2. Define Workflow
@workflow(name="user_onboarding", version="1.0.0")
class OnboardingWorkflow:
    """User onboarding process with parallel initialization."""
    steps = [
        # Fan-out: 'create' triggers 3 steps at once
        Step(
            name="create", 
            task_name="create_account", 
            next_steps=["setup_perms", "welcome_email", "profile"]
        ),
        
        # These 3 run in parallel (in a real worker environment)
        Step(name="setup_perms", task_name="setup_permissions", next_steps=["activate"]),
        Step(name="welcome_email", task_name="send_welcome_email", next_steps=["activate"]),
        Step(name="profile", task_name="create_user_profile", next_steps=["activate"]),
        
        # Join/Barrier: 'activate' waits for all 3 to complete
        Step(
            name="activate", 
            task_name="activate_account", 
            wait_for=["setup_perms", "welcome_email", "profile"]
        ),
    ]

if __name__ == "__main__":
    print("\n--- Running Parallel Onboarding Workflow ---")
    wf = registry.get_workflow("user_onboarding", "1.0.0")
    engine = WorkflowEngine()
    
    # execute_workflow simulation handles 'wait_for' synchronization
    final_context = engine.execute_workflow(wf, {})
    
    print(f"--- Workflow Finished. Final Context: {final_context} ---")

"""
Output esperado:

--- Running Parallel Onboarding Workflow ---
Executing step: create (task: create_account)
 [Step] Creating user account in database...
Executing step: setup_perms (task: setup_permissions)
 [Step] Setting up default permissions (Parallel)...
Executing step: welcome_email (task: send_welcome_email)
 [Step] Sending welcome email (Parallel)...
Executing step: profile (task: create_user_profile)
 [Step] Initializing user profile (Parallel)...
Executing step: activate (task: activate_account)
 [Step] All parallel tasks finished. ACTIVATING ACCOUNT.
--- Workflow Finished. Final Context: {'user_id': 42, 'username': 'ezranieri', 'perms_ok': True, 'email_sent': True, 'profile_created': True, 'status': 'ACTIVE'} ---
"""
