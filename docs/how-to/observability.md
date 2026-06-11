# How-to: Observability and Tracing

Flowcore provides built-in support for distributed tracing using **OpenTelemetry**. This allows you to visualize the execution flow of your workflows across the API and multiple workers.

## Enabling Tracing

Tracing is enabled by default. You can control it using environment variables:

```env
OTEL_ENABLED=true
OTEL_SERVICE_NAME=flowcore
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```

To disable tracing, set `OTEL_ENABLED=false`.

## Using Jaeger

The best way to visualize traces is using **Jaeger**. When running in **Full Mode** (`docker-compose.full.yml`), Jaeger is included automatically.

1. **Start the stack:**
   ```bash
   docker-compose -f docker-compose.full.yml up -d
   ```
2. **Execute a workflow:**
   ```bash
   flowcore run order_process
   ```
3. **Open Jaeger UI:**
   Navigate to `http://localhost:16686` in your browser.

## What's in a Trace?

A single workflow execution trace typically contains:
- **`workflow.start`**: The initial API request and Celery task trigger.
- **`step.execute`**: One span for each step in the workflow.
- **Attributes:**
  - `workflow.name`: Name of the workflow.
  - `workflow.execution_id`: ID of the execution.
  - `step.name`: Name of the current step.
  - `worker.id`: Hostname of the worker that executed the step.

## Error Tracking
If a step fails, the span will be marked as an error, and the exception details (message and stack trace) will be attached to the span attributes, making it easy to debug distributed failures.

---

## Performance Monitoring
By analyzing the duration of `step.execute` spans, you can identify bottlenecks in your workflow and optimize task execution times.
