.PHONY: help install install-dev lint format test test-cov clean build docs security audit performance
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev,test,docs]"

lint: ## Run all linting tools
	@echo "Running Ruff linter..."
	ruff check src tests
	@echo "Running MyPy type checker..."
	mypy src
	@echo "Running docstring linter..."
	pydocstyle src

format: ## Format code with ruff
	ruff format src tests
	ruff check --fix src tests

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=my_coding_agent --cov-report=html --cov-report=term-missing

test-fast: ## Run tests excluding slow ones
	pytest -m "not slow"

performance: ## Run performance benchmarks
	pytest --benchmark-only tests/benchmarks/

security: ## Run security analysis
	@echo "Running Bandit security linter..."
	bandit -r src/
	@echo "Running safety check..."
	safety check
	@echo "Running pip-audit..."
	pip-audit

audit: security ## Alias for security

docs: ## Generate documentation
	@echo "Building Sphinx documentation..."
	cd docs && make clean && make html
	@echo "Documentation built in docs/_build/html/"

docs-live: ## Build docs and serve locally with auto-reload
	cd docs && make livehtml

docs-linkcheck: ## Check for broken links in documentation
	cd docs && make linkcheck

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean ## Build the package
	python -m build

release: ## Build and upload to PyPI (requires proper credentials)
	make build
	python -m twine upload dist/*

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

check-all: lint test security ## Run all checks (linting, tests, security)

setup-dev: install-dev pre-commit-install ## Complete development setup 