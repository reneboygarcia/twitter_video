## Learned User Preferences
* Prefer simplicity over complexity.
* Implement one clear purpose per unit of code to maximize readability and minimize cognitive load.
* Follow the Single Responsibility and Open/Closed Principles with clear, minimal abstractions.
* Choose explicit, predictable control flow and logic over implicit behavior.
* Embed runtime checks, validate invariants, and implement comprehensive unit tests for edge cases.
* Follow strict testing discipline: tests are immutable; iterate on production code until tests pass, and never relax test expectations unless the specification changes or the test contract itself is wrong.
* Write meaningful, self-explanatory names and concise docstrings, utilizing inline comments only for complex logic.
* Solve issues methodically step-by-step and perform continuous refactoring before optimizing.
* Avoid code bloat, eliminate redundancy, and minimize external dependencies.
* Challenge the existing implementation during reviews to simplify relentlessly and ensure immediate comprehension.
* Do not prompt to confirm or clarify assumptions; choose the most reasonable assumption, proceed, and document it.

## Learned Workspace Facts
* The project is a Rust-based Twitter/X Video Downloader CLI tool (`twitdl`).
* Source files are located under the `src/` directory:
  * [src/lib.rs](file:///Users/reneboygarcia/Documents/Github%20Projects/Twitter%20Video%20Downloader/src/lib.rs): Library entry exposing the modules.
  * [src/main.rs](file:///Users/reneboygarcia/Documents/Github%20Projects/Twitter%20Video%20Downloader/src/main.rs): CLI entry point parsing arguments via `clap` and prompting via `inquire`.
  * [src/downloader.rs](file:///Users/reneboygarcia/Documents/Github%20Projects/Twitter%20Video%20Downloader/src/downloader.rs): `yt-dlp` wrapper, progress parser, path-safety check, and drop-guard cleanup logic.
  * [src/update_checker.rs](file:///Users/reneboygarcia/Documents/Github%20Projects/Twitter%20Video%20Downloader/src/update_checker.rs): 24-hour update checker with GitHub Releases API integration.
* External dependencies:
  * `yt-dlp`: Executed via subprocess (system dependency).
  * Rust crates: `clap` (CLI), `inquire` (prompts), `indicatif` (progress), `ureq` (requests), `serde`/`serde_json` (JSON), `dirs` (folders), `ctrlc` (signal handling).
* A virtual environment named `venv/` supports running the Python benchmark/time trial script [tests/benchmark.py](file:///Users/reneboygarcia/Documents/Github%20Projects/Twitter%20Video%20Downloader/tests/benchmark.py).
* A `Makefile` manages developer workflows: `setup`, `clean`, `format`, `test`, `build`, `install`, `sca`, `sbom`, and `pre-merge`.
* Execution logs are written to platform logs paths (e.g. `~/Library/Logs/twitdl/download.log` on macOS) with local fallbacks.
* Pytest-based tests have been replaced by a native Cargo-based integration test suite:
  * [tests/downloader_tests.rs](file:///Users/reneboygarcia/Documents/Github%20Projects/Twitter%20Video%20Downloader/tests/downloader_tests.rs): Verifies URL parsing, path traversal blocklists, and subprocess behaviors.
  * [tests/update_checker_tests.rs](file:///Users/reneboygarcia/Documents/Github%20Projects/Twitter%20Video%20Downloader/tests/update_checker_tests.rs): Verifies caching and update version calculations.
* A Homebrew Formula is maintained in `Formula/twitdl.rb` and links to a local tap `reneboygarcia/tap` at `/opt/homebrew/Library/Taps/reneboygarcia/homebrew-tap`. It builds the binary from source using standard Cargo installation and depends on `yt-dlp`.
* A Trivy configuration `trivy.yaml` excludes local cargo build/target and virtualenv directories from vulnerability scans.
