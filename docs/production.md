# Production Deployment Guide

This guide covers configuration and best practices for running Flowcore in a production environment, beyond the local `make up` development stack.

## 1. Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg for API, auto-converted to psycopg2 for workers) | `postgresql+asyncpg://user:pass@host:5432/flowcore_db` |
| `CELERY_BROKER_URL` | Message broker for Celery (Redis or RabbitMQ) | `redis://host:6379/0` or `amqp://user:pass@host:5672//` |
| `CELERY_RESULT_BACKEND` | Backend for Celery task results | `redis://host:6379/0` |
| `OTEL_ENABLED` | Enable/disable OpenTelemetry tracing | `true` |
| `OTEL_SERVICE_NAME` | Service name reported to the tracing backend | `flowcore-api` / `flowcore-worker` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP gRPC endpoint for trace export (e.g. Jaeger) | `http://jaeger:4317` |
| `LOG_LEVEL` | Application log level | `info` |
| `DEBUG` | Enable debug mode (must be `false` in production) | `false` |

> ⚠️ **Never use the default credentials** from `docker-compose.yml` (`flowcore` / `flowcore_password`, `guest` / `guest`) in production. Use a secrets manager (e.g. AWS Secrets Manager, Vault, Kubernetes Secrets) to inject credentials at runtime.

## 2. Database

- Use a managed PostgreSQL instance (e.g. AWS RDS, Cloud SQL) rather than the containerized `db` service.
- Run migrations before starting the API/worker containers:
```bash
  uv run alembic upgrade head
```
- The API uses the **asyncpg** driver, while workers use **psycopg2** (sync). Both are derived automatically from a single `DATABASE_URL` by `flowcore.infrastructure.db.session` — you only need to set one variable.

## 3. Message Broker

Flowcore supports two broker configurations, matching `docker-compose.yml` (Redis-only) and `docker-compose.full.yml` (RabbitMQ + Redis result backend):

- **Redis-only**: simplest setup, suitable for smaller deployments.
- **RabbitMQ + Redis**: recommended for higher throughput, as RabbitMQ provides more robust message acknowledgment guarantees for Celery.

## 4. Workers

Celery workers can be scaled horizontally — each step of a workflow runs as an independent task, so adding more worker replicas increases parallel step throughput.

When a worker starts, it performs an **auto-discovery** of workflow and task definitions and resets any steps stuck in `RUNNING` state back to `PENDING`, allowing recovery after a crash or restart.

## 5. Observability

- Set `OTEL_ENABLED=true` and point `OTEL_EXPORTER_OTLP_ENDPOINT` to a production-grade tracing backend (Jaeger, Tempo, or any OTLP-compatible collector).
- Use distinct `OTEL_SERVICE_NAME` values for the API and worker services (e.g. `flowcore-api`, `flowcore-worker`) to distinguish them in traces.
- See [Observability How-to](how-to/observability.md) for details on what each trace contains.

## 6. Health Checks

The API exposes a `/health` endpoint suitable for liveness/readiness probes in container orchestrators:

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

## 7. Multi-Tenancy

If running a multi-tenant deployment, ensure all client requests include the `X-Tenant-ID` header. See [Multi-tenancy How-to](how-to/multi-tenancy.md) for isolation details.

## 8. Security Checklist

- [ ] `DEBUG=false`
- [ ] Database credentials managed via secrets, not hardcoded
- [ ] Broker credentials managed via secrets
- [ ] `/health` endpoint exposed only to internal load balancer / orchestrator, not public internet
- [ ] TLS termination handled by a reverse proxy / load balancer (Flowcore does not handle TLS itself)
