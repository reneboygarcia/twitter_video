.PHONY: setup clean install test format help dev sca sbom pre-merge

# Python and environment settings
PYTHON := python3
VENV_NAME := venv
VENV_BIN := $(VENV_NAME)/bin
PROJECT_NAME := twitter_video_dl
SRC_DIR := src/$(PROJECT_NAME)

help:
	@echo "🛠️  Twitter Video Downloader"
	@echo "==========================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make dev-setup - Create virtual environment and install all dependencies (including dev tools)"
	@echo ""
	@echo "Development & Security Commands:"
	@echo "  make clean     - Remove all build artifacts and caches"
	@echo "  make test      - Run test suite with pytest"
	@echo "  make format    - Format code with black and isort"
	@echo "  make sca       - Run Trivy vulnerability scan (CRITICAL,HIGH; exit 1 if found)"
	@echo "  make sbom      - Generate CycloneDX SBOM (Trivy) to sbom.cyclonedx.json"
	@echo "  make pre-merge - Run quality gates: test and sca"
	@echo ""
	@echo "Getting Started:"
	@echo "1. Run 'make dev-setup' to create environment and install dependencies"
	@echo "2. Run 'source venv/bin/activate' to activate environment" 
	@echo "3. Run 'twitdl' to start the downloader (interactive by default, or pass URL directly)"
	@echo ""
	@echo "For more details, visit: https://github.com/reneboygarcia/twitter_video"

dev-setup:
	@echo "📦 Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV_NAME)
	@echo "✅ Virtual environment created!"
	@echo "🔧 Installing dependencies..."
	@. $(VENV_NAME)/bin/activate && \
		pip install --upgrade pip && \
		pip install -e ".[dev]" && \
		echo "✅ Development environment ready!"
	@echo "\033[0;32m🚀 To activate: source $(VENV_NAME)/bin/activate"
	@echo "🚀 Then run: twitdl --guided\033[0m"

clean:
	@echo "🧹 Cleaning project..."
	rm -rf $(VENV_NAME)
	rm -rf *.egg-info dist build
	rm -f *.spec
	rm -rf .pytest_cache .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f sbom.cyclonedx.json
	@echo "✨ Project cleaned!"

format:
	@echo "🎨 Formatting code..."
	$(VENV_BIN)/black $(SRC_DIR) tests
	$(VENV_BIN)/isort $(SRC_DIR) tests
	@echo "✅ Code formatted!"


test:
	@echo "🧪 Running tests..."
	$(VENV_BIN)/pytest tests -v
	@echo "✅ Tests completed!"

build-bin:
	@echo "⚙️ Compiling standalone binary..."
	$(VENV_BIN)/pyinstaller --onedir --clean --name twitdl --paths src twitdl_bin.py
	@echo "✅ Standalone binary built at ./dist/twitdl!"

test-bin: build-bin
	@echo "🧪 Running standalone binary verification and time trials..."
	$(VENV_BIN)/python -m pytest tests/test_binary.py -v -s

install:
	$(VENV_BIN)/pip install .

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

# When SKIP_SCA=1, skip Trivy (e.g. local Docker/Trivy DB issues).
pre-merge: test $(if $(SKIP_SCA),,sca)
	@echo "✅ All pre-merge checks passed!"