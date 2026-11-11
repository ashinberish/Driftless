.DEFAULT_GOAL := help
COMPOSE := docker compose -f deploy/docker-compose.yml

.PHONY: help setup infra-up infra-down stack-up api worker web test test-integration lint typecheck fmt build ci

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies (uv + pnpm) and git hooks
	cd backend && uv sync
	cd frontend && pnpm install
	-pre-commit install

infra-up: ## Start databases + Temporal for local development
	$(COMPOSE) up -d

infra-down: ## Stop local infrastructure
	$(COMPOSE) down

stack-up: ## Run the whole stack in containers
	$(COMPOSE) --profile app up -d --build

api: ## Run the API with reload (http://localhost:8000/api/v1/docs)
	cd backend && uv run uvicorn driftless_api.main:create_app --factory --reload

worker: ## Run the Temporal worker
	cd backend && uv run driftless-worker

web: ## Run the web app (http://localhost:5173)
	cd frontend && pnpm dev

test: ## Run unit tests (backend + frontend)
	cd backend && uv run pytest -m "not integration"
	cd frontend && pnpm test

test-integration: ## Run tests that need real databases (make infra-up first)
	cd backend && uv run pytest -m integration

lint: ## Lint everything
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && pnpm lint

typecheck: ## Type-check everything
	cd backend && uv run pyright
	cd frontend && pnpm typecheck

fmt: ## Auto-format backend code
	cd backend && uv run ruff check --fix . && uv run ruff format .

build: ## Production build of the web app
	cd frontend && pnpm build

ci: lint typecheck test build ## Everything CI runs
