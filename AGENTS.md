## Learned User Preferences
* Prefer simplicity over complexity.
* Implement one clear purpose per unit of code to maximize readability and minimize cognitive load.
* Follow the Single Responsibility and Open/Closed Principles with clear, minimal abstractions.
* Choose explicit, predictable control flow and logic over implicit behavior.
* Embed runtime checks, validate invariants, and implement comprehensive unit tests for edge cases.
* Write meaningful, self-explanatory names and concise docstrings, utilizing inline comments only for complex logic.
* Solve issues methodically step-by-step and perform continuous refactoring before optimizing.
* Avoid code bloat, eliminate redundancy, and minimize external dependencies.
* Challenge the existing implementation during reviews to simplify relentlessly and ensure immediate comprehension.
* Do not prompt to confirm or clarify assumptions; choose the most reasonable assumption, proceed, and document it.

## Learned Workspace Facts
* The project is a Python-based Twitter/X Video Downloader CLI tool.
* Codebase is structured as an editable package with sources under the `src/` directory.
* Entry point is the command line executable `twitdl`, which triggers `twitter_video_dl.cli:main`.
* The CLI uses `questionary` for interactive prompts and `rich` for terminal UI formatting.
* Backend video extraction and downloading are powered by `yt-dlp` in `downloader.py`.
* Development dependencies include `black`, `isort`, `flake8`, `mypy`, `pytest`, and `coverage`.
* A virtual environment named `venv` is expected at the root of the project.
* A Makefile manages workflow actions: `dev-setup`, `clean`, `format`, `test`, and `install`.
* Execution logs are written locally to `download.log`.
