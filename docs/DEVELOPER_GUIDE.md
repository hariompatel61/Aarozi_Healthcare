# Aarozi Healthcare — Developer Guide

## 1. Local Development Setup
- **Prerequisites**: Python 3.11+, Node.js 20+, Docker & Docker Compose.
- **Install Python dependencies**: `pip install -e ./apps/api -e .`
- **Install Node dependencies**: `npm install`
- **Start Infrastructure (Postgres, Redis, MinIO)**: `docker compose -f docker-compose.dev.yml up -d`
- **Run API**: `uvicorn app.main:app --reload --app-dir apps/api`
- **Run Web**: `npm run dev --workspace=apps/web`

## 2. Running Tests
- **Backend tests**: `python -m pytest apps/api/tests -q`
- **Linting**: `ruff check apps/api contracts tools`
- **Type checking**: `mypy apps/api/app contracts`

## 3. Troubleshooting
- **Database connection error**: Ensure Docker container `aarozi-postgres` is running and `DATABASE_URL` matches.
- **Port already in use**: Check if another instance of Postgres (5432) or Redis (6379) or API (8000) is running.

## 4. Branch and Commit Conventions
- **Branches**: `feature/Pxx-xx-short-description`, `fix/Pxx-xx-issue`, `release/v1.0.0`
- **Commits**: Conventional commits format: `feat(api): add patient registration endpoint`, `fix(db): handle session rollback correctly`.