.DEFAULT_GOAL := help
SHELL         := /bin/bash
PYTHON        ?= python3
PIP           ?= pip

.PHONY: help install install-dev dev test test-ci lint format type-check \
        docker-up docker-down docker-logs clean

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Install ───────────────────────────────────────────────────────────────────

install: ## Install runtime dependencies
	$(PIP) install -e .

install-dev: ## Install runtime + dev dependencies
	$(PIP) install -e ".[dev,eval]"

# ── Development ───────────────────────────────────────────────────────────────

dev: ## Start backend with hot-reload (requires .env)
	uvicorn chronos.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Start Vite dev server for the frontend
	cd chronos-frontend && npm install && npm run dev

# ── Testing ───────────────────────────────────────────────────────────────────

test: ## Run full test suite
	pytest tests/ -v

test-ci: ## Run tests in CI mode (no colour, fail fast)
	pytest tests/ -x --tb=short -q

test-unit: ## Run only unit tests (no integration markers)
	pytest tests/ -v -m "not integration"

# ── Code quality ──────────────────────────────────────────────────────────────

lint: ## Run ruff linter
	ruff check chronos/ tests/

format: ## Auto-format with ruff
	ruff format chronos/ tests/

type-check: ## Run mypy type checker
	mypy chronos/ --ignore-missing-imports

check: lint type-check ## Run linter + type checker together

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up: ## Start all services with docker-compose
	docker compose up --build -d

docker-down: ## Stop and remove containers
	docker compose down

docker-logs: ## Tail container logs
	docker compose logs -f chronos

docker-reset: ## Stop containers and delete volumes
	docker compose down -v

# ── MCP ───────────────────────────────────────────────────────────────────────

mcp: ## Start the CHRONOS MCP server (stdio transport)
	chronos-mcp

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean: ## Remove build artefacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
