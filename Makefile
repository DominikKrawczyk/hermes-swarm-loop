# Hermes Swarm Loop — Makefile
# Development automation for the 3×3×3×N framework

.PHONY: help setup test lint clean install push run-ci

help:  # Show available targets
	@grep -E '^[a-zA-Z_-]+:.*#.*$$' $(MAKEFILE_LIST) | sort | awk '{printf "  %-20s %s\n", $$1, $$2}'

setup:  # Create venv and install dependencies
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@echo "Setup complete. Activate: source .venv/bin/activate"

install:  # Install dependencies into active venv
	pip install -r requirements.txt

test:  # Run all tests
	python3 -m pytest tests/ -v --tb=short

test-cov:  # Run tests with coverage
	python3 -m pytest tests/ -v --tb=short --cov=engine --cov=scaling --cov=configs --cov-report=term-missing

lint:  # Lint all Python files
	python3 -m ruff check engine/ scaling/ tests/ configs/ scripts/ --fix

typecheck:  # Run mypy type checking
	python3 -m mypy engine/ scaling/ scripts/ --ignore-missing-imports

clean:  # Remove cache and temp files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .coverage htmlcov/

push:  # Push to GitHub (uses gh api blob→tree→commit→ref pipeline)
	python3 scripts/github_push.py

run-ci:  # Full CI pipeline
	python3 -m pytest tests/ -v --tb=short --cov=engine --cov=scaling --cov=configs
	python3 -m ruff check engine/ scaling/

bootstrap:  # Run bootstrap launcher
	python3 scripts/bootstrap.py --project-name "MyProject" --project-desc "Build something great"

bootstrap-init:  # Run bootstrap with init-only (setup DB + phase config, skip launch)
	python3 scripts/bootstrap.py --project-name "MyProject" --project-desc "Build something great" --init-only
