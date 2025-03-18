# Default variables
python := "python3"
pkg_manager := "uv"

# Show help by default
default:
    @just --list

# Install git-stats
install:
    @echo "Installing git-stats using {{pkg_manager}}..."
    {{pkg_manager}} tool install . -e --reinstall

# Run tests
test:
    @echo "Running tests..."
    uv run pytest

# Run tests with coverage
test-cov:
    @echo "Running tests with coverage..."
    uv run pytest --cov=git_stats

# Run linting
lint:
    @echo "Running linting..."
    uvx ruff format
    uvx ruff check --fix

# Clean build artifacts
clean:
    @echo "Cleaning build artifacts..."
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    find . -name "__pycache__" -exec rm -rf {} +
    find . -name "*.pyc" -delete
    find . -name ".pytest_cache" -exec rm -rf {} +
    find . -name ".coverage" -delete
