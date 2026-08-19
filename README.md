<p align="left">
  <img src="./banner/banner_twitter.png" alt="Twitter Video Downloader Banner" style="max-width: 100%;"/>
</p>

# Twitter video downloader CLI

[![CI (Test + SCA + SBOM)](https://github.com/reneboygarcia/twitter_video/actions/workflows/ci.yml/badge.svg)](https://github.com/reneboygarcia/twitter_video/actions/workflows/ci.yml)
[![CodeQL](https://github.com/reneboygarcia/twitter_video/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/reneboygarcia/twitter_video/actions/workflows/codeql-analysis.yml)

A command-line tool written in Rust to download videos from Twitter and X using `yt-dlp`.

For details on why we migrated from Python to Rust, read the [Rust Transition Report](docs/RUST_TRANSITION.md).

---

## Features

- **Interactive mode**: Guided prompt flow powered by inquire.
- **Direct command mode**: Download media immediately by passing a tweet URL (e.g., `twitdl <url>`).
- **Progress indicator**: Real-time progress bars powered by indicatif.
- **Quality selection**: Select `best`, `medium`, or `low` video quality.
- **Custom output path**: Save files to your Downloads directory or specify a custom output path.
- **Built-in update command**: Run `twitdl update` to check for updates and upgrade your installation.
- **Shell completions**: Generate completion scripts for Zsh, Bash, Fish, or PowerShell.
- **Safety checks**: Restricts write access to system directories and cleans up incomplete download files on exit.
- **Platform support**: Runs on macOS, Linux, and Windows.

---

## Performance comparison

We rewrote the command-line tool in Rust to reduce startup overhead and binary size.

* **Startup time**: Reduced from 364 ms in Python to 6.3 ms in Rust.
* **Binary size**: Reduced from 20.0 MB to 3.75 MB as a standalone binary.

---

## Installation

### Using Homebrew on macOS or Linux

You can install the tool from Homebrew using the tap path:

```sh
brew install reneboygarcia/tap/twitdl
```

Or you can tap the repository first, and then run install:

```sh
brew tap reneboygarcia/tap
brew install twitdl
```

Once installed, you can start the application from your terminal by running:

```sh
twitdl
```

### Manual installation from source

#### Prerequisites
1. **Rust toolchain**: Install Rust and Cargo from [rust-lang.org](https://www.rust-lang.org/tools/install).
2. **Subprocess dependency**: Install `yt-dlp` on your system so it is available in your PATH.

#### Installation steps
First, clone the repository:

```sh
git clone https://github.com/reneboygarcia/twitter_video.git
cd twitter_video
```

Second, build the release binary:

```sh
make build
```

Third, install the binary locally:

```sh
make install
```

---

## Usage

### Interactive mode

Run `twitdl` without arguments to start the interactive prompt:

```sh
twitdl
```

### Direct command mode

Download a video immediately by providing the tweet URL and optional arguments:

```sh
twitdl <tweet-url> --quality best --output ~/Desktop/video.mp4
```

#### Command options:
- `-q, --quality <QUALITY>`: Video quality settings (`best`, `medium`, `low`).
- `-o, --output <PATH>`: Custom output directory or file path.
- `-g, --guide`: Force interactive guided mode.
- `-u, --update`: Check for updates and upgrade.
- `-V, --version`: Print version information.
- `-h, --help`: Show help text.

---

## Updating and upgrading

You can check for updates and upgrade your installation directly from the terminal.

Run the update command:

```sh
twitdl update
```

If you installed the tool through Homebrew, `twitdl update` will run `brew upgrade reneboygarcia/tap/twitdl` for you.

To check for available updates without performing an upgrade, run:

```sh
twitdl update --check-only
```

---

## Shell completions

You can generate shell completion scripts for your shell.

To generate completions for Zsh, run:

```sh
twitdl completions zsh > ~/.zsh/completion/_twitdl
```

Supported shell options are `zsh`, `bash`, `fish`, and `powershell`.

---

## Security and verification

This repository includes security audits and path safety checks.

- **Automated scanning**: Trivy scans for dependency vulnerabilities and generates Software Bill of Materials (SBOM) files on every build.
- **CodeQL analysis**: GitHub CodeQL runs static code analysis on pushes and pull requests.
- **Input validation**: The application prevents path traversal attempts and blocks writing to system folders.

---

## Development

Developer workflows are defined in the [Makefile](Makefile).

- Main CLI entry point: [src/main.rs](src/main.rs)
- Media download engine: [src/downloader.rs](src/downloader.rs)
- Update checker module: [src/update_checker.rs](src/update_checker.rs)
- Integration test suite: [tests/](tests/)

---

## Author

[Reneboy Garcia](https://github.com/reneboygarcia)
