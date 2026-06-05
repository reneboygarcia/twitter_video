# Twitter Video Downloader Developer Guide (CLAUDE.md)

This guide documents the development, build, test, and code style guidelines for the Twitter Video Downloader.

## Command Reference

### Environment Setup
*   **Complete developer setup (venv, deps, dev-deps, editable install):**
    ```bash
    make dev-setup
    ```
*   **Manual virtual environment activation:**
    ```bash
    source venv/bin/activate
    ```

### Execution
*   **Run the CLI tool directly (requires active virtual environment):**
    ```bash
    twitdl
    ```
*   **Run the CLI tool interactive guided mode:**
    ```bash
    twitdl --guide
    ```

### Testing
*   **Run pytest test suite:**
    ```bash
    make test
    ```
    or manually:
    ```bash
    venv/bin/pytest tests -v
    ```

#### Test Discipline
*   **Immutable Tests**: Tests are considered the source of truth contract. If a test fails and its expectation is correct, do not modify or relax the test. Instead, iterate on and fix the production code until the test passes.
*   **When to edit tests**: Only adjust or update test cases when the specification itself changes, or if the test was written against the wrong contract/API.
*   **Isolation**: Keep unit and integration tests focused and isolated.

### Linting, Formatting, & Type Checking
*   **Format code (Black & isort):**
    ```bash
    make format
    ```
*   **Lint check:**
    ```bash
    venv/bin/flake8 src/
    ```
*   **Static type checking:**
    ```bash
    venv/bin/mypy src/
    ```

### Cleanup
*   **Remove build artifacts, caches, and virtual environment:**
    ```bash
    make clean
    ```

---

## Code Style & Architecture

### Python Version Support
*   Targeting Python 3.12

### Formatting
*   Use **Black** for code styling (default 88 characters line limit).
*   Use **isort** for import ordering.
*   Formatting check runs during CI/CD or PR verification.

### Design Principles
*   **Simplicity**: Prefer explicit over implicit logic, minimize abstractions, and follow the Single Responsibility Principle.
*   **Error Handling**: Decorate CLI interaction methods with grace handlers (`@handle_errors`, `@handle_back_option`) to capture and print informative messages instead of raw tracebacks.
*   **Logging**: Keep log calls clean. Logs are written automatically to `download.log` and printed to standard output.
*   **User Interface**: Maintain interactive prompts with `questionary` and stylized outputs using `rich`. Keep interface layouts clean and user friendly.
