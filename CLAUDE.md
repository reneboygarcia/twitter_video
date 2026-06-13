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

# context-mode — MANDATORY routing rules

You have context-mode MCP tools available. These rules are NOT optional — they protect your context window from flooding. A single unrouted command can dump 56 KB into context and waste the entire session.

## BLOCKED commands — do NOT attempt these

### curl / wget — BLOCKED
Any Bash command containing `curl` or `wget` is intercepted and replaced with an error message. Do NOT retry.
Instead use:
- `ctx_fetch_and_index(url, source)` to fetch and index web pages
- `ctx_execute(language: "javascript", code: "const r = await fetch(...)")` to run HTTP calls in sandbox

### Inline HTTP — BLOCKED
Any Bash command containing `fetch('http`, `requests.get(`, `requests.post(`, `http.get(`, or `http.request(` is intercepted and replaced with an error message. Do NOT retry with Bash.
Instead use:
- `ctx_execute(language, code)` to run HTTP calls in sandbox — only stdout enters context

### WebFetch — BLOCKED
WebFetch calls are denied entirely. The URL is extracted and you are told to use `ctx_fetch_and_index` instead.
Instead use:
- `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` to query the indexed content

## REDIRECTED tools — use sandbox equivalents

### Bash (>20 lines output)
Bash is ONLY for: `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`, and other short-output commands.
For everything else, use:
- `ctx_batch_execute(commands, queries)` — run multiple commands + search in ONE call
- `ctx_execute(language: "shell", code: "...")` — run in sandbox, only stdout enters context

### Read (for analysis)
If you are reading a file to **Edit** it → Read is correct (Edit needs content in context).
If you are reading to **analyze, explore, or summarize** → use `ctx_execute_file(path, language, code)` instead. Only your printed summary enters context. The raw file content stays in the sandbox.

### Grep (large results)
Grep results can flood context. Use `ctx_execute(language: "shell", code: "grep ...")` to run searches in sandbox. Only your printed summary enters context.

## Tool selection hierarchy

1. **GATHER**: `ctx_batch_execute(commands, queries)` — Primary tool. Runs all commands, auto-indexes output, returns search results. ONE call replaces 30+ individual calls.
2. **FOLLOW-UP**: `ctx_search(queries: ["q1", "q2", ...])` — Query indexed content. Pass ALL questions as array in ONE call.
3. **PROCESSING**: `ctx_execute(language, code)` | `ctx_execute_file(path, language, code)` — Sandbox execution. Only stdout enters context.
4. **WEB**: `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` — Fetch, chunk, index, query. Raw HTML never enters context.
5. **INDEX**: `ctx_index(content, source)` — Store content in FTS5 knowledge base for later search.

## Subagent routing

When spawning subagents (Agent/Task tool), the routing block is automatically injected into their prompt. Bash-type subagents are upgraded to general-purpose so they have access to MCP tools. You do NOT need to manually instruct subagents about context-mode.

## Output constraints

- Keep responses under 500 words.
- Write artifacts (code, configs, PRDs) to FILES — never return them as inline text. Return only: file path + 1-line description.
- When indexing content, use descriptive source labels so others can `ctx_search(source: "label")` later.

## ctx commands

| Command | Action |
|---------|--------|
| `ctx stats` | Call the `ctx_stats` MCP tool and display the full output verbatim |
| `ctx doctor` | Call the `ctx_doctor` MCP tool, run the returned shell command, display as checklist |
| `ctx upgrade` | Call the `ctx_upgrade` MCP tool, run the returned shell command, display as checklist |
