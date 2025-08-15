.PHONY: setup clean install test format help dev

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
	@echo "Development Commands:"
	@echo "  make clean     - Remove all build artifacts and caches"
	@echo "  make test      - Run test suite with pytest"
	@echo "  make format    - Format code with black and isort"
	@echo ""
	@echo "Getting Started:"
	@echo "1. Run 'make dev-setup' to create environment and install dependencies"
	@echo "2. Run 'source venv/bin/activate' to activate environment" 
	@echo "3. Run 'twitdl --guided' to start the interactive downloader"
	@echo ""
	@echo "For more details, visit: https://github.com/yourusername/twitter-video-dl"

dev-setup: clean
	@echo "📦 Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV_NAME)
	@echo "✅ Virtual environment created!"
	@echo "🔧 Installing dependencies..."
	@. $(VENV_NAME)/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements.txt && \
		pip install -e . && \
		echo "✨ Setup complete!" && \
		echo "🔧 Installing development dependencies..." && \
		pip install -e ".[dev]" && \
		echo "✅ Development environment ready!"
	@echo "\033[0;32m🚀 To activate the virtual environment, run: source $(VENV_NAME)/bin/activate"
	@echo "🚀 Then, you can now run: twitdl --guided\033[0m"

clean:
	@echo "🧹 Cleaning project..."
	rm -rf $(VENV_NAME)
	rm -rf *.egg-info dist build
	rm -rf .pytest_cache .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✨ Project cleaned!"

format:
	@echo "🎨 Formatting code..."
	$(VENV_BIN)/black $(SRC_DIR)
	$(VENV_BIN)/isort $(SRC_DIR)
	@echo "✅ Code formatted!"

test:
	@echo "🧪 Running tests..."
	$(VENV_BIN)/pytest tests -v
	@echo "✅ Tests completed!"

install:
	$(VENV_BIN)/pip install .