up:
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down

test:
	python -m pytest

lint-api:
	ruff check apps/api

typecheck-api:
	python -m mypy apps/api/app
