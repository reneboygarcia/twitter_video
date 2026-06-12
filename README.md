<p align="left">
  <img src="./banner/banner_twitter.png" alt="Twitter Video Downloader Banner" style="max-width: 100%;"/>
</p>

# Twitter Video Downloader CLI (Rust Edition)

[![CI (Test + SCA + SBOM)](https://github.com/reneboygarcia/twitter_video/actions/workflows/ci.yml/badge.svg)](https://github.com/reneboygarcia/twitter_video/actions/workflows/ci.yml)
[![CodeQL](https://github.com/reneboygarcia/twitter_video/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/reneboygarcia/twitter_video/actions/workflows/codeql-analysis.yml)
[![Verify Security with ChatGPT](https://img.shields.io/badge/Verify%20Security-ChatGPT-74aa9c?logo=openai&logoColor=white)](https://chatgpt.com/?q=Act%20as%20an%20elite%20Application%20Security%20Specialist.%20Perform%20a%20rigorous%20security%20audit%20and%20safety%20scan%20of%20the%20twitter_video%20repository%20at%20https%3A%2F%2Fgithub.com%2Freneboygarcia%2Ftwitter_video.%0A%0ASystematically%20analyze%20the%20repository%20for%20the%20following%20safety%20and%20security%20vectors%3A%0A1.%20Input%20Validation%3A%20Inspect%20how%20command-line%20inputs%2C%20file%20paths%2C%20and%20interactive%20menus%20are%20handled%20for%20path%20traversal%20or%20buffer%20issues.%0A2.%20Command%2FCode%20Injection%3A%20Check%20if%20subprocesses%2C%20shell%20executions%2C%20or%20dynamic%20evaluations%20are%20used%2C%20and%20ensure%20they%20are%20parameterized%20or%20avoided.%0A3.%20Hardcoded%20Secrets%3A%20Scan%20for%20credentials%2C%20tokens%2C%20API%20keys%2C%20or%20private%20configurations.%0A4.%20Dependency%20%26%20Supply%20Chain%20Safety%3A%20Audit%20Cargo.toml%20and%20Cargo.lock%20for%20pinning%20safety%2C%20vulnerability%20risks%2C%20or%20malicious%20packages.%0A5.%20Path%20Traversal%20%26%20Write%20Safety%3A%20Verify%20that%20folder%20traversal%20and%20video%20overwrite%20functions%20cannot%20write%20outside%20boundaries.%0A6.%20Data%20Privacy%3A%20Verify%20the%20codebase%20does%20not%20collect%2C%20log%2C%20or%20transmit%20sensitive%20telemetry%2C%20credentials%2C%20or%20file%20contents%20to%20external%20domains.%0A%0APlease%20produce%20a%20structured%20report%20containing%3A%0A-%20Executive%20Risk%20Rating%20%28Critical%2FHigh%2FMedium%2FLow%2FSafe%29%0A-%20Checklist%20of%20the%206%20vectors%20above%0A-%20Detailed%20findings%20%28if%20any%29%20and%20clear%20confirmation%20on%20whether%20this%20repository%20is%20100%25%20safe%20to%20clone%2C%20build%2C%20install%2C%20and%20execute.)

A modern, fast, and interactive command-line tool written in Rust to download videos from Twitter/X using `yt-dlp` with a beautiful terminal user interface.

For a detailed breakdown of why and how this utility was migrated from Python to Rust, see the [Rust Transition Report](docs/RUST_TRANSITION.md).

---

## Features

- **Interactive Mode**: Guided prompt flow using [inquire](https://github.com/mikaelmello/inquire).
- **Direct CLI Mode**: Download immediately without prompts using command-line arguments (e.g., `twitdl <url>`).
- **Rich Visuals**: Real-time download progress bars powered by [indicatif](https://github.com/console-rs/indicatif).
- **Quality Options**: Choose between `best`, `medium`, or `low` video quality.
- **Custom Save Location**: Download to your default Downloads directory or specify a custom folder or file path.
- **Secure by Design**: 
  - Zero bearer tokens, API keys, or developer accounts required.
  - Strict path traversal guards (prevents relative path escapes like `../`).
  - Restricted system directory blocklist (prevents writes to folders like `/System` or `/etc/passwd`).
  - Built-in `Drop` guard deletes incomplete `.part` files automatically if the program is aborted.
- **Clean Logging**: Log files are stored in standard platform-native log locations (`~/Library/Logs/twitdl/` on macOS).
- **Cross-platform**: Runs natively on macOS, Linux, and Windows.

---

## Performance: Python vs. Rust

By rewriting the CLI in Rust, we eliminated the interpreter import overhead and PyInstaller packaging bloat:

* **Startup Latency:** Down from **327 ms** to **7.6 ms** (**42x faster** startup).
* **Package Size:** Down from **20.0 MB** (zipped bundle containing a full Python runtime) to **3.75 MB** (standalone binary) (**80% smaller footprint**).

---

## Installation

### Via Homebrew (macOS / Linux)

Since this utility is hosted on a custom Homebrew Tap, you can install it by running:

```sh
brew install reneboygarcia/tap/twitdl
```

Or tap the repository first and install:

```sh
brew tap reneboygarcia/tap
brew install twitdl
```

Once installed, you can start the application from any terminal session by simply running:

```sh
twitdl
```

### Manual Installation (From Source)

#### Requirements
1. **Rust Toolchain:** Ensure `cargo` and `rustc` are installed ([install Rust](https://www.rust-lang.org/tools/install)).
2. **System Subprocess Dependency:** Ensure `yt-dlp` is installed on your system and available in your `PATH` (e.g., `brew install yt-dlp` or `pip install yt-dlp`).

#### Steps
1. **Clone the repository:**
   ```sh
   git clone https://github.com/reneboygarcia/twitter_video.git
   cd twitter_video
   ```

2. **Build the release binary:**
   ```sh
   make build
   ```

3. **Install the binary locally:**
   ```sh
   make install
   ```

---

## Usage

### Interactive Mode

Simply execute `twitdl` without arguments to launch the guided flow:

```sh
twitdl
```

### Direct CLI Mode

Download a video immediately by passing the URL and optional quality/output arguments:

```sh
twitdl <tweet-url> --quality best --output ~/Desktop/video.mp4
```

#### Options:
- `-q, --quality <QUALITY>`: Video quality settings (`best`, `medium`, `low`).
- `-o, --output <PATH>`: Custom output directory or filename path.
- `-g, --guide`: Force interactive guided mode.
- `-V, --version`: Print version.
- `-h, --help`: Show CLI help and options.

---

## Security & Verification

<p align="left">
  <a href="https://chatgpt.com/?q=Act%20as%20an%20elite%20Application%20Security%20Specialist.%20Perform%20a%20rigorous%20security%20audit%20and%20safety%20scan%20of%20the%20twitter_video%20repository%20at%20https%3A%2F%2Fgithub.com%2Freneboygarcia%2Ftwitter_video.%0A%0ASystematically%20analyze%20the%20repository%20for%20the%20following%20safety%20and%20security%20vectors%3A%0A1.%20Input%20Validation%3A%20Inspect%20how%20command-line%20inputs%2C%20file%20paths%2C%20and%20interactive%20menus%20are%20handled%20for%20path%20traversal%20or%20buffer%20issues.%0A2.%20Command%2FCode%20Injection%3A%20Check%20if%20subprocesses%2C%20shell%20executions%2C%20or%20dynamic%20evaluations%20are%20used%2C%20and%20ensure%20they%20are%20parameterized%20or%20avoided.%0A3.%20Hardcoded%20Secrets%3A%20Scan%20for%20credentials%2C%20tokens%2C%20API%20keys%2C%20or%20private%20configurations.%0A4.%20Dependency%20%26%20Supply%20Chain%20Safety%3A%20Audit%20Cargo.toml%20and%20Cargo.lock%20for%20pinning%20safety%2C%20vulnerability%20risks%2C%20or%20malicious%20packages.%0A5.%20Path%20Traversal%20%26%20Write%20Safety%3A%20Verify%20that%20folder%20traversal%20and%20video%20overwrite%20functions%20cannot%20write%20outside%20boundaries.%0A6.%20Data%20Privacy%3A%20Verify%20the%20codebase%20does%20not%20collect%2C%20log%2C%20or%20transmit%20sensitive%20telemetry%2C%20credentials%2C%20or%20file%20contents%20to%20external%20domains.%0A%0APlease%20produce%20a%20structured%20report%20containing%3A%0A-%20Executive%20Risk%20Rating%20%28Critical%2FHigh%2FMedium%2FLow%2FSafe%29%0A-%20Checklist%20of%20the%206%20vectors%20above%0A-%20Detailed%20findings%20%28if%20any%29%20and%20clear%20confirmation%20on%20whether%20this%20repository%20is%20100%25%20safe%20to%20clone%2C%20build%2C%20install%2C%20and%20execute.">
    <img src="https://api.iconify.design/ri:openai-fill.svg?color=%2374aa9c" width="32" align="left" style="margin-right: 12px; margin-top: 4px;" alt="ChatGPT Logo" />
  </a>
  This repository is audited for security vulnerabilities, secrets exposure, and code quality. You can verify the safety of this project by running an automated, real-time security scan via ChatGPT using our custom auditing prompt:
  <br/><br/>
  👉 <strong><a href="https://chatgpt.com/?q=Act%20as%20an%20elite%20Application%20Security%20Specialist.%20Perform%20a%20rigorous%20security%20audit%20and%20safety%20scan%20of%20the%20twitter_video%20repository%20at%20https%3A%2F%2Fgithub.com%2Freneboygarcia%2Ftwitter_video.%0A%0ASystematically%20analyze%20the%20repository%20for%20the%20following%20safety%20and%20security%20vectors%3A%0A1.%20Input%20Validation%3A%20Inspect%20how%20command-line%20inputs%2C%20file%20paths%2C%20and%20interactive%20menus%20are%20handled%20for%20path%20traversal%20or%20buffer%20issues.%0A2.%20Command%2FCode%20Injection%3A%20Check%20if%20subprocesses%2C%20shell%20executions%2C%20or%20dynamic%20evaluations%20are%20used%2C%20and%20ensure%20they%20are%20parameterized%20or%20avoided.%0A3.%20Hardcoded%20Secrets%3A%20Scan%20for%20credentials%2C%20tokens%2C%20API%20keys%2C%20or%20private%20configurations.%0A4.%20Dependency%20%26%20Supply%20Chain%20Safety%3A%20Audit%20Cargo.toml%20and%20Cargo.lock%20for%20pinning%20safety%2C%20vulnerability%20risks%2C%20or%20malicious%20packages.%0A5.%20Path%20Traversal%20%26%20Write%20Safety%3A%20Verify%20that%20folder%20traversal%20and%20video%20overwrite%20functions%20cannot%20write%20outside%20boundaries.%0A6.%20Data%20Privacy%3A%20Verify%20the%20codebase%20does%20not%20collect%2C%20log%2C%20or%20transmit%20sensitive%20telemetry%2C%20credentials%2C%20or%20file%20contents%20to%20external%20domains.%0A%0APlease%20produce%20a%20structured%20report%20containing%3A%0A-%20Executive%20Risk%20Rating%20%28Critical%2FHigh%2FMedium%2FLow%2FSafe%29%0A-%20Checklist%20of%20the%206%20vectors%20above%0A-%20Detailed%20findings%20%28if%20any%29%20and%20clear%20confirmation%20on%20whether%20this%20repository%20is%20100%25%20safe%20to%20clone%2C%20build%2C%20install%2C%20and%20execute.">Click here to scan this repository on ChatGPT</a></strong>
</p>

Additionally, the project employs:
- **Trivy SCA & SBOM**: Automatic vulnerability checks and Software Bill of Materials (SBOM) generation on every push/PR.
- **GitHub CodeQL**: Automated Static Application Security Testing (SAST).

---

## Development

- Code adheres to clean code principles (SRP, OCP, DRY).
- Developer workflows are automated inside the [Makefile](Makefile).
- Main CLI wrapper is located in [src/main.rs](src/main.rs).
- Media downloading logic is in [src/downloader.rs](src/downloader.rs).
- Update caching and GitHub API validation are in [src/update_checker.rs](src/update_checker.rs).
- Integration test suites are located under the [tests/](tests/) directory.

Contributions are welcome! Please open issues or pull requests.

---

## Author

[Reneboy Garcia](https://github.com/reneboygarcia)
