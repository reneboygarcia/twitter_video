.PHONY: setup clean install test format help build sca sbom pre-merge

help:
	@echo "🛠️  Twitter Video Downloader (Rust Edition)"
	@echo "==========================================="
	@echo ""
	@echo "Setup & Build Commands:"
	@echo "  make setup     - Install formatting tools or dependencies"
	@echo "  make build     - Build release binary in ./target/release/"
	@echo ""
	@echo "Development & Security Commands:"
	@echo "  make clean     - Remove cargo build artifacts"
	@echo "  make test      - Run all cargo unit and integration tests"
	@echo "  make format    - Format all rust files using cargo fmt"
	@echo "  make sca       - Run Trivy vulnerability scan (CRITICAL,HIGH; exit 1 if found)"
	@echo "  make sbom      - Generate CycloneDX SBOM (Trivy) to sbom.cyclonedx.json"
	@echo "  make pre-merge - Run quality gates: test, format check, and sca"
	@echo ""
	@echo "Getting Started:"
	@echo "1. Run 'cargo run' to start the interactive downloader"
	@echo "2. Run 'cargo run -- <url>' to download a video directly"
	@echo ""
	@echo "For more details, visit: https://github.com/reneboygarcia/twitter_video"

setup:
	rustup component add rustfmt 2>/dev/null || true

clean:
	@echo "🧹 Cleaning project..."
	cargo clean
	rm -f sbom.cyclonedx.json
	@echo "✨ Project cleaned!"

format:
	@echo "🎨 Formatting code..."
	cargo fmt
	@echo "✅ Code formatted!"

test:
	@echo "🧪 Running tests..."
	cargo test
	@echo "✅ Tests completed!"

build:
	@echo "⚙️ Compiling standalone release binary..."
	cargo build --release
	@echo "✅ Standalone binary built at ./target/release/twitdl!"

install:
	@echo "📦 Installing binary locally..."
	cargo install --path .
	@echo "✅ Installed successfully!"

sca:
	@echo "🔍 Running Trivy vulnerability scan (CRITICAL,HIGH)..."
	@if ! command -v trivy >/dev/null 2>&1; then \
		echo "⚠️  Trivy is not installed. Install it with: brew install trivy"; exit 1; \
	fi
	trivy fs --scanners vuln --severity CRITICAL,HIGH --exit-code 1 .

sbom:
	@echo "📋 Generating CycloneDX SBOM..."
	@if ! command -v trivy >/dev/null 2>&1; then \
		echo "⚠️  Trivy is not installed. Install it with: brew install trivy"; exit 1; \
	fi
	trivy fs -f cyclonedx -o sbom.cyclonedx.json .
	@echo "✅ SBOM written to sbom.cyclonedx.json"

pre-merge: test $(if $(SKIP_SCA),,sca)
	@echo "🎨 Checking formatting..."
	cargo fmt -- --check
	@echo "✅ All pre-merge checks passed!"