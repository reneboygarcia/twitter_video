# Homebrew Core submission guide for `twitdl`

This document provides step-by-step instructions to submit `twitdl` to [Homebrew/homebrew-core](https://github.com/Homebrew/homebrew-core) so users worldwide can run `brew install twitdl` without adding a custom tap.

---

## Formula details

- **Name**: `twitdl`
- **Location in Homebrew Core**: `Formula/t/twitdl.rb`
- **License**: MIT
- **Dependencies**: `rust` (build time), `yt-dlp` (runtime)

---

## Formula template (`Formula/t/twitdl.rb`)

```ruby
class Twitdl < Formula
  desc "Interactive CLI tool to download videos from Twitter/X"
  homepage "https://github.com/reneboygarcia/twitter_video"
  url "https://github.com/reneboygarcia/twitter_video/archive/refs/tags/v0.2.7.tar.gz"
  sha256 "02ab5e5ea24cb0d79078b61e52ecd1bab3ad94dd00a5c6ec2f71f0fbc92e6dde"
  license "MIT"
  head "https://github.com/reneboygarcia/twitter_video.git", branch: "main"

  depends_on "rust" => :build
  depends_on "yt-dlp"

  def install
    system "cargo", "install", *std_cargo_args
    bin.install_symlink bin/"twitdl" => "td"
  end

  def caveats
    <<~EOS
      Once installed, you can start twitdl from your terminal:

      Interactive mode:
        twitdl  (or 'td')

      Direct download mode:
        twitdl <tweet-url>

      Check for updates / upgrade:
        twitdl update

      For full usage options:
        twitdl --help
    EOS
  end

  test do
    system bin/"twitdl", "--help"
    system bin/"td", "--help"
  end
end
```

---

## Submission steps

### 1. Fork Homebrew Core
Visit [github.com/Homebrew/homebrew-core](https://github.com/Homebrew/homebrew-core) and click **Fork**.

### 2. Clone your fork and create a branch
In your terminal, run:

```bash
git clone https://github.com/reneboygarcia/homebrew-core.git
cd homebrew-core
git checkout -b add-twitdl-0.2.7
```

### 3. Add the formula file
Copy the formula file to the `Formula/t/` directory:

```bash
mkdir -p Formula/t
cp /path/to/twitter_video/Formula/twitdl.rb Formula/t/twitdl.rb
```

### 4. Verify locally
Run strict verification using Homebrew CLI:

```bash
# Test build from source
brew install --build-from-source Formula/t/twitdl.rb

# Run formula tests
brew test Formula/t/twitdl.rb

# Audit formula against Homebrew rules
brew audit --strict --online Formula/t/twitdl.rb
```

### 5. Commit and push
Commit the change and push to your fork:

```bash
git add Formula/t/twitdl.rb
git commit -m "twitdl 0.2.7 (new formula)"
git push origin add-twitdl-0.2.7
```

### 6. Open Pull Request
Open a pull request to `Homebrew/homebrew-core` using GitHub or `gh`:

```bash
gh pr create --repo Homebrew/homebrew-core \
  --title "twitdl 0.2.7 (new formula)" \
  --body "New formula submission for twitdl, an interactive Rust CLI tool to download Twitter/X videos using yt-dlp."
```

---

## Verification checklist

- [x] Formula URL points to official GitHub release archive (`v0.2.7.tar.gz`).
- [x] Formula SHA-256 checksum matches release archive.
- [x] Formula passes `brew audit --strict twitdl` with 0 warnings.
- [x] Formula test block passes cleanly for both `twitdl` and `td`.
- [x] Open source license (MIT) specified.
