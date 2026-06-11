# Configuration Reference

Flowcore is configured primarily through environment variables.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy connection string for PostgreSQL. | `postgresql://flowcore:flowcore_password@localhost:5432/flowcore_db` |
| `CELERY_BROKER_URL` | Connection URL for Celery broker (Redis or RabbitMQ). | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Connection URL for Celery result storage. | `redis://localhost:6379/0` |
| `OTEL_ENABLED` | Whether to enable OpenTelemetry tracing. | `true` |
| `OTEL_SERVICE_NAME` | Name of the service in traces. | `flowcore` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP gRPC endpoint for trace export. | `http://jaeger:4317` |
| `STUCK_STEP_TIMEOUT_MINUTES` | Time after which a "RUNNING" step is considered stuck and reset to "PENDING" on worker startup. | `15` |
| `LOG_LEVEL` | Logging level (debug, info, warning, error). | `info` |
| `DEBUG` | Enable debug mode for FastAPI. | `false` |

---

## Deployment Modes

Flowcore supports two main deployment modes via Docker Compose.

### 1. Lite Mode
Optimized for local development and simple workloads.

**Components:**
- **PostgreSQL:** State persistence.
- **Redis:** Used as both Celery broker and result backend.
- **API:** FastAPI server.
- **Worker:** Celery worker.

**To run:**
```bash
docker-compose up -d
```

### 2. Full Mode
Optimized for production-like environments with enhanced observability.

**Components:**
- **PostgreSQL:** State persistence.
- **RabbitMQ:** High-performance message broker for Celery.
- **Redis:** Dedicated result backend.
- **Jaeger:** Distributed tracing UI and collector.
- **API & Worker:** Scalable services.

**To run:**
```bash
docker-compose -f docker-compose.full.yml up -d
```

---

## Observability

When `OTEL_ENABLED=true`, Flowcore automatically instruments:
1. **FastAPI:** Every incoming request to the API.
2. **Celery Tasks:** Every workflow execution and step execution.
3. **Database Calls:** SQLAlchemy operations (if instrumented in `tracing.py`).

Traces are sent to the `OTEL_EXPORTER_OTLP_ENDPOINT`. In **Full Mode**, you can view these traces by visiting `http://localhost:16686` (Jaeger UI).
