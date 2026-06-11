# How-to: Multi-Tenancy

Flowcore is designed from the ground up to support multi-tenant environments. Data isolation is achieved through the `tenant_id` field in every execution record.

## Default Tenant
If no tenant is specified, Flowcore uses `default` as the tenant ID.

## Using the CLI
When running or querying workflows via the CLI, use the `--tenant` (or `-t`) flag.

```bash
# Start a workflow for tenant 'acme'
flowcore run order_process -t acme

# List executions for tenant 'globex'
flowcore list --tenant globex
```

## Using the API
The Flowcore API expects the `X-Tenant-ID` header for all execution-related requests.

```http
POST /workflows/order_process/run
X-Tenant-ID: acme-corp
Content-Type: application/json

{
  "context": {"order_id": 123}
}
```

## Data Isolation
- **Executions:** Each `WorkflowExecution` is tagged with a `tenant_id`.
- **Querying:** Repositories filter by `tenant_id` automatically when a tenant is provided in the request context.
- **Worker:** The worker processes tasks for all tenants but maintains the `tenant_id` context throughout the execution lifecycle.

## Why use Multi-Tenancy?
1. **SaaS Applications:** Host multiple customers on the same Flowcore instance while keeping their data separate.
2. **Environment Isolation:** Use different tenants for `dev`, `staging`, and `prod` within the same cluster.
3. **Departmental Scaling:** Separate workflows for `HR`, `Finance`, and `Engineering`.
