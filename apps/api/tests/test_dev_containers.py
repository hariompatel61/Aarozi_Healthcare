"""P01-02 dev containers structural tests.

All tests are offline-safe — no live Docker, database, or Redis required.
They verify that the devcontainer configuration files, docker-compose
services, and Alembic scaffold are present and structurally correct.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def _repo(rel: str) -> Path:
    return _repo_root / rel


# ---------------------------------------------------------------------------
# .devcontainer structure
# ---------------------------------------------------------------------------

def test_devcontainer_directory_exists() -> None:
    assert _repo(".devcontainer").is_dir()


def test_devcontainer_json_exists() -> None:
    assert _repo(".devcontainer/devcontainer.json").is_file()


def test_devcontainer_dockerfile_exists() -> None:
    assert _repo(".devcontainer/Dockerfile").is_file()


def test_devcontainer_json_is_valid() -> None:
    data = json.loads(
        _repo(".devcontainer/devcontainer.json").read_text(encoding="utf-8")
    )
    assert "name" in data
    assert "dockerComposeFile" in data or "image" in data or "build" in data


def test_devcontainer_references_compose_file() -> None:
    data = json.loads(
        _repo(".devcontainer/devcontainer.json").read_text(encoding="utf-8")
    )
    compose_ref = data.get("dockerComposeFile", "")
    assert "docker-compose" in compose_ref


def test_devcontainer_specifies_workspace_folder() -> None:
    data = json.loads(
        _repo(".devcontainer/devcontainer.json").read_text(encoding="utf-8")
    )
    assert "workspaceFolder" in data
    assert data["workspaceFolder"].startswith("/workspaces")


def test_devcontainer_specifies_post_create_command() -> None:
    data = json.loads(
        _repo(".devcontainer/devcontainer.json").read_text(encoding="utf-8")
    )
    assert "postCreateCommand" in data


def test_devcontainer_dockerfile_uses_python_311() -> None:
    content = _repo(".devcontainer/Dockerfile").read_text(encoding="utf-8")
    assert "python:3.11" in content.lower()


def test_devcontainer_dockerfile_installs_node() -> None:
    content = _repo(".devcontainer/Dockerfile").read_text(encoding="utf-8")
    assert "node" in content.lower() or "nodejs" in content.lower()


# ---------------------------------------------------------------------------
# .env.example completeness
# ---------------------------------------------------------------------------

def test_env_example_exists() -> None:
    assert _repo(".env.example").is_file()


@pytest.mark.parametrize("key", [
    "APP_ENV",
    "DATABASE_URL",
    "REDIS_URL",
    "OBJECT_STORAGE_ENDPOINT",
    "OBJECT_STORAGE_BUCKET",
    "JWT_SECRET",
])
def test_env_example_contains_key(key: str) -> None:
    content = _repo(".env.example").read_text(encoding="utf-8")
    assert key in content, f".env.example is missing key: {key}"


def test_env_example_not_committed_as_env() -> None:
    """The .gitignore must block .env but allow .env.example."""
    gitignore = _repo(".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    assert "!.env.example" in gitignore


# ---------------------------------------------------------------------------
# Alembic scaffold presence
# ---------------------------------------------------------------------------

def test_alembic_ini_exists() -> None:
    assert _repo("apps/api/alembic.ini").is_file()


def test_alembic_env_py_exists() -> None:
    assert _repo("apps/api/alembic/env.py").is_file()


def test_alembic_ini_has_script_location() -> None:
    content = _repo("apps/api/alembic.ini").read_text(encoding="utf-8")
    assert "script_location" in content


def test_alembic_env_py_reads_database_url_from_env() -> None:
    content = _repo("apps/api/alembic/env.py").read_text(encoding="utf-8")
    assert "DATABASE_URL" in content
    assert (
        "os.environ" in content
        or "getenv" in content
        or "environ.get" in content
    )


def test_alembic_env_py_no_hardcoded_credentials() -> None:
    content = _repo("apps/api/alembic/env.py").read_text(encoding="utf-8")
    for pat in ["password=", "passwd=", "aarozi:aarozi"]:
        assert pat not in content, (
            f"alembic/env.py must not contain hard-coded credential: {pat!r}"
        )


# ---------------------------------------------------------------------------
# docker-compose.dev.yml services
# ---------------------------------------------------------------------------

def test_docker_compose_file_exists() -> None:
    assert _repo("docker-compose.dev.yml").is_file()


def test_docker_compose_has_postgres_service() -> None:
    content = _repo("docker-compose.dev.yml").read_text(encoding="utf-8")
    assert "postgres" in content


def test_docker_compose_has_redis_service() -> None:
    content = _repo("docker-compose.dev.yml").read_text(encoding="utf-8")
    assert "redis" in content


def test_docker_compose_has_minio_service() -> None:
    content = _repo("docker-compose.dev.yml").read_text(encoding="utf-8")
    assert "minio" in content


def test_docker_compose_has_api_service() -> None:
    content = _repo("docker-compose.dev.yml").read_text(encoding="utf-8")
    assert "api:" in content


def test_docker_compose_postgres_has_healthcheck() -> None:
    content = _repo("docker-compose.dev.yml").read_text(encoding="utf-8")
    assert "pg_isready" in content or "healthcheck" in content


def test_docker_compose_redis_has_healthcheck() -> None:
    content = _repo("docker-compose.dev.yml").read_text(encoding="utf-8")
    assert content.count("healthcheck") >= 2


def test_docker_compose_no_hardcoded_production_secrets() -> None:
    content = _repo("docker-compose.dev.yml").read_text(encoding="utf-8")
    for word in ["secret-prod", "live-secret", "production-key"]:
        assert word not in content.lower()
