# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import os
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .routes import workflows
from ..worker.celery_app import celery_app
from ... import demo  # Import demo workflows
from ...observability.tracing import setup_tracing

# Initialize tracing
setup_tracing("flowcore-api")

app = FastAPI(
    title="Flowcore API",
    description="Distributed and Durable Workflow Engine",
    version="0.1.0"
)

# Instrument FastAPI
if os.getenv("OTEL_ENABLED", "true").lower() == "true":
    FastAPIInstrumentor.instrument_app(app)

# Register routes
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

