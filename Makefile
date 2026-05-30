.PHONY: help up down test lint format migrate demo

help:
	@echo "Flowcore Makefile commands:"
	@echo "  up      : Start the MVP stack (Docker Compose Lite)"
	@echo "  down    : Stop all containers"
	@echo "  test    : Run tests using pytest"
	@echo "  lint    : Run ruff for linting"
	@echo "  format  : Run ruff for formatting"
	@echo "  migrate : Run alembic migrations"
	@echo "  demo    : Alias for 'up'"

up:
	docker-compose up -d

down:
	docker-compose down

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

migrate:
	uv run alembic upgrade head

demo: up
