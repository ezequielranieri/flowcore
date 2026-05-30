# Contributing to Flowcore

We welcome contributions to Flowcore! Whether you're fixing a bug, adding a feature, or improving documentation, here's how you can help.

## Development Workflow

1. **Fork the Repository**: Create a fork of the `flowcore` repository.
2. **Clone your Fork**:
   ```bash
   git clone <your-fork-url>
   cd flowcore
   ```
3. **Setup Environment**:
   - Ensure you have `uv` installed.
   - Run `uv sync` to install dependencies.
4. **Create a Branch**: Use a descriptive branch name (e.g., `feature/add-new-dashboard` or `fix/persistence-bug`).
5. **Make Changes**: Implement your changes.
6. **Run Tests**:
   ```bash
   make test
   ```
7. **Lint & Format**:
   ```bash
   make lint
   make format
   ```
8. **Submit a Pull Request**: Push your branch and open a Pull Request against the `main` branch of the original repository.

## Standards

- **Code Style**: We use `ruff` for linting and formatting. Ensure your code passes all checks.
- **Tests**: Every new feature or bug fix must include corresponding tests in the `tests/` directory.
- **Documentation**: Update the README or other documentation files if your changes affect how Flowcore is used or installed.

Thank you for contributing!
