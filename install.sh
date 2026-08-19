#!/usr/bin/env bash
set -e

REPO="reneboygarcia/twitter_video"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"

echo "📥 Installing twitdl..."

# Detect OS and Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Darwin)
    PLATFORM="macos"
    ;;
  Linux)
    PLATFORM="linux"
    ;;
  *)
    echo "❌ Unsupported operating system: $OS"
    exit 1
    ;;
esac

case "$ARCH" in
  x86_64)
    ARCH_NAME="x86_64"
    ;;
  arm64|aarch64)
    ARCH_NAME="arm64"
    ;;
  *)
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

# Get latest release tag from GitHub
LATEST_TAG=$(curl -sL "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_TAG" ]; then
  echo "⚠️ Could not resolve latest release version tag. Falling back to v0.2.7."
  LATEST_TAG="v0.2.7"
fi

VERSION="${LATEST_TAG#v}"
TARBALL="twitdl-${PLATFORM}-${ARCH_NAME}.tar.gz"
DOWNLOAD_URL="https://github.com/reneboygarcia/twitter_video/releases/download/${LATEST_TAG}/${TARBALL}"

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "📦 Downloading twitdl ${LATEST_TAG} for ${PLATFORM}-${ARCH_NAME}..."

if curl -sL "$DOWNLOAD_URL" -o "$TEMP_DIR/$TARBALL"; then
  tar -xzf "$TEMP_DIR/$TARBALL" -C "$TEMP_DIR"
  
  if [ ! -w "$INSTALL_DIR" ]; then
    echo "🔑 Requesting sudo permission to install binary into $INSTALL_DIR..."
    sudo mv "$TEMP_DIR/twitdl" "$INSTALL_DIR/twitdl"
    sudo chmod +x "$INSTALL_DIR/twitdl"
    sudo ln -sf "$INSTALL_DIR/twitdl" "$INSTALL_DIR/td"
  else
    mv "$TEMP_DIR/twitdl" "$INSTALL_DIR/twitdl"
    chmod +x "$INSTALL_DIR/twitdl"
    ln -sf "$INSTALL_DIR/twitdl" "$INSTALL_DIR/td"
  fi

  echo "✔ Successfully installed twitdl to $INSTALL_DIR/twitdl"
  echo "✔ Created short command alias 'td' -> '$INSTALL_DIR/twitdl'"
  echo ""
  echo "Run 'twitdl' or 'td' to start!"
else
  echo "⚠️ Binary release archive not found for ${PLATFORM}-${ARCH_NAME}. Building from source via cargo..."
  if command -v cargo >/dev/null 2>&1; then
    cargo install --git "https://github.com/reneboygarcia/twitter_video.git" twitdl
    echo "✔ Successfully installed twitdl via cargo!"
  else
    echo "❌ Cargo not found. Please install Rust from https://rust-lang.org or install Homebrew."
    exit 1
  fi
fi
