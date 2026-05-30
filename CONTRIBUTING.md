# Contributing to Flowcore

Contributions to Flowcore are welcome! Whether fixing a bug, adding a feature, or improving documentation, the following guide outlines the process.

## Development Workflow

1. **Fork the Repository**: Create a fork of the `flowcore` repository.
2. **Clone the Fork**:
   ```bash
   git clone <your-fork-url>
   cd flowcore
   ```
3. **Setup Environment**:
   - Ensure `uv` is installed.
   - Run `uv sync` to install dependencies.
4. **Create a Branch**: Use a descriptive branch name (e.g., `feature/add-new-dashboard` or `fix/persistence-bug`).
5. **Make Changes**: Implement the necessary changes.
6. **Run Tests**:
   ```bash
   make test
   ```
7. **Lint & Format**:
   ```bash
   make lint
   make format
   ```
8. **Submit a Pull Request**: Push the branch and open a Pull Request against the `main` branch of the original repository.

## Standards

- **Code Style**: `ruff` is used for linting and formatting. Ensure code passes all checks.
- **Tests**: Every new feature or bug fix must include corresponding tests in the `tests/` directory.
- **Documentation**: Update the README or other documentation files if changes affect how Flowcore is used or installed.

Thank you for contributing!
