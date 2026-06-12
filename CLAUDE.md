# Twitter Video Downloader Developer Guide (CLAUDE.md)

This guide documents the development, build, test, and code style guidelines for the Rust-based `twitdl` Twitter Video Downloader.

## Command Reference

### Environment Setup & Installation
*   **Compile and install standalone release binary to PATH (via Cargo):**
    ```bash
    make install
    ```
    or manually:
    ```bash
    cargo install --path .
    ```

### Execution
*   **Run interactive guided mode:**
    ```bash
    cargo run
    ```
*   **Run direct download mode:**
    ```bash
    cargo run -- <tweet-url>
    ```
*   **Run installed/Homebrew binary:**
    ```bash
    twitdl <tweet-url>
    ```

### Testing
*   **Run all unit and integration tests:**
    ```bash
    make test
    ```
    or manually:
    ```bash
    cargo test
    ```

#### Test Discipline
*   **Immutable Tests**: Tests are considered the source of truth contract. If a test fails and its expectation is correct, do not modify or relax the test. Instead, iterate on and fix the production code until the test passes.
*   **When to Edit Tests**: Only adjust or update test cases when the specification itself changes, or if the test was written against the wrong contract/API.
*   **Isolation**: Keep unit and integration tests focused and isolated.

### Formatting, Linting, & Security
*   **Format code (rustfmt):**
    ```bash
    make format
    ```
    or manually:
    ```bash
    cargo fmt
    ```
*   **Check formatting without modifying files:**
    ```bash
    cargo fmt -- --check
    ```
*   **Run Trivy vulnerability scan (CRITICAL,HIGH; exit 1 if found):**
    ```bash
    make sca
    ```
*   **Generate CycloneDX SBOM (Trivy) to sbom.cyclonedx.json:**
    ```bash
    make sbom
    ```
*   **Run pre-merge checks (test, sca, formatting checks):**
    ```bash
    make pre-merge
    ```

### Cleanup
*   **Remove cargo build artifacts and local SBOM outputs:**
    ```bash
    make clean
    ```

---

## Code Style & Architecture

### Rust Version & Toolchain
*   Targeting Rust 2021 Edition.
*   Uses standard `cargo fmt` for formatting.

### Design Principles & Modules
*   **Simplicity**: Prefer explicit over implicit logic, minimize abstractions, and follow the Single Responsibility Principle.
*   **Downloader Module (`src/downloader.rs`)**:
    *   Subprocess wrapper around system dependency `yt-dlp`.
    *   Reads stdout of `yt-dlp --progress-template "%(progress)j"` as JSON lines for real-time `indicatif` progress bar updates.
    *   Applies path traversal prevention and critical system directories blocklists.
    *   Implements `CleanupGuard` utilizing Rust's `Drop` trait to clean up incomplete `.part` files on failure/interrupt.
*   **Update Checker Module (`src/update_checker.rs`)**:
    *   Checks for newer releases against the GitHub API.
    *   Caches update check status locally for 24 hours (`update_cache.json` in system caches dir).
*   **Main Module (`src/main.rs`)**:
    *   CLI entry point using `clap` for direct execution arguments.
    *   Uses `inquire` for interactive prompts and guided user flows.
*   **Logging**: Logs are written to platform-specific log paths (e.g. `~/Library/Logs/twitdl/download.log` on macOS) with local fallback.
