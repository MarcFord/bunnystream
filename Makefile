# Makefile for bunnystream package

.PHONY: help test lint build release-patch release-minor release-major

# Default target
help:
	@echo "Available commands:"
	@echo "  test           - Run tests with coverage"
	@echo "  lint           - Run code quality checks"
	@echo "  build          - Build the package"
	@echo "  release-patch  - Create a patch release (x.y.Z)"
	@echo "  release-minor  - Create a minor release (x.Y.0)"
	@echo "  release-major  - Create a major release (X.0.0)"
	@echo "  clean          - Clean build artifacts"

# Test the package
test:
	uv run pytest --cov=src/bunnystream --cov-report=term-missing -v

# Run linting
lint:
	uv run pylint src/bunnystream/ --output-format=text
	uv run black --check src/ tests/
	uv run isort --check-only src/ tests/
	uv run mypy src/bunnystream/
	uv run bandit -r src/bunnystream/
	uv run flake8 src/ tests/

# Build the package
build:
	uv build

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

# Release commands
release-patch:
	@echo "Creating patch release..."
	python scripts/bump_version.py patch

release-minor:
	@echo "Creating minor release..."
	python scripts/bump_version.py minor

release-major:
	@echo "Creating major release..."
	python scripts/bump_version.py major

# Install development dependencies
install-dev:
	uv sync --all-extras

# Run all checks before release
pre-release: test lint
	@echo "✅ All checks passed! Ready for release."
