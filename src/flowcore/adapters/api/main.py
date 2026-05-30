# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

from fastapi import FastAPI
from .routes import workflows
from ..worker.celery_app import celery_app
from ... import demo  # Import demo workflows

app = FastAPI(
    title="Flowcore API",
    description="Distributed and Durable Workflow Engine",
    version="0.1.0"
)

# Register routes
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

