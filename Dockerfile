# Use a slim Python image
FROM python:3.11-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project files
COPY pyproject.toml .
# If we had a lockfile: COPY uv.lock .

# Install dependencies using uv
# --system flag to install into the system python environment since we are in a container
RUN uv pip install --system --no-cache -e .

# Copy the rest of the application
COPY src/ src/

# Set Python path
ENV PYTHONPATH=/app/src

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "flowcore.adapters.api:app", "--host", "0.0.0.0", "--port", "8000"]
