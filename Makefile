# ---------------------------------------------------------------------------
# Aarozi Healthcare – monorepo Makefile
# ---------------------------------------------------------------------------
# Python tooling operates from the repo root (pyproject.toml lives here).
# Node/npm workspaces are defined in root package.json.
# ---------------------------------------------------------------------------

.PHONY: up down \
        install install-api install-web \
        run-api run-web \
        test test-api \
        lint lint-api lint-web \
        typecheck-api \
        format format-api \
        migrate-up migrate-down \
        clean

# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------
up:
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
install: install-api install-web

install-api:
	pip install -e ./apps/api -e .

install-web:
	npm install

# ---------------------------------------------------------------------------
# Run (development servers)
# ---------------------------------------------------------------------------
run-api:
	uvicorn app.main:app --reload --app-dir apps/api

run-web:
	npm run dev --workspace=apps/web

# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------
test: test-api

test-api:
	python -m pytest apps/api/tests -q

# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------
lint: lint-api lint-web

lint-api:
	ruff check apps/api contracts tools

lint-web:
	npm run lint --workspace=apps/web --if-present

lint-all:
	npm run lint:all --if-present

# ---------------------------------------------------------------------------
# Type-check
# ---------------------------------------------------------------------------
typecheck-api:
	python -m mypy apps/api/app contracts

# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------
format: format-api

format-api:
	ruff format apps/api contracts tools

# ---------------------------------------------------------------------------
# Database migrations (Alembic)
# ---------------------------------------------------------------------------
migrate-up:
	alembic -c apps/api/alembic.ini upgrade head

migrate-down:
	alembic -c apps/api/alembic.ini downgrade -1

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache  -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache  -exec rm -rf {} + 2>/dev/null || true

