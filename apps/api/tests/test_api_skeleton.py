"""Tests for P01-04 API Skeleton.

Covers:
- Router registration and URL structure
- Shared response schemas (APIResponse, ErrorResponse, PaginatedResponse)
- Custom exception hierarchy (AppError and subclasses)
- Error handler shapes (404, 422, 500, AppError subclasses)
- RequestIDMiddleware (X-Request-ID, X-Response-Time headers)
- create_app factory produces a valid FastAPI instance
- Docs URLs hidden in production mode
- No duplicate routes registered
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import (
    AppError,
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
    register_exception_handlers,
)
from app.main import app, create_app
from app.schemas import APIResponse, ErrorDetail, ErrorResponse, PaginatedResponse
from app.settings import Settings

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Schema unit tests
# ---------------------------------------------------------------------------


class TestAPIResponseSchema:
    def test_ok_flag_defaults_true(self) -> None:
        r: APIResponse[dict] = APIResponse(data={"x": 1})
        assert r.ok is True

    def test_data_field_stored(self) -> None:
        r: APIResponse[str] = APIResponse(data="hello")
        assert r.data == "hello"

    def test_serialises_to_dict(self) -> None:
        d = APIResponse(data=42).model_dump()
        assert d == {"ok": True, "data": 42}


class TestErrorDetailSchema:
    def test_requires_code_and_message(self) -> None:
        e = ErrorDetail(code="not_found", message="Thing not found")
        assert e.code == "not_found"
        assert e.field is None

    def test_optional_field_stored(self) -> None:
        e = ErrorDetail(code="validation_error", message="Bad value", field="email")
        assert e.field == "email"


class TestErrorResponseSchema:
    def test_ok_flag_is_false(self) -> None:
        r = ErrorResponse(error=ErrorDetail(code="x", message="y"))
        assert r.ok is False

    def test_round_trips_dict(self) -> None:
        d = ErrorResponse(
            error=ErrorDetail(code="not_found", message="Not found", field=None)
        ).model_dump()
        assert d["ok"] is False
        assert d["error"]["code"] == "not_found"
        assert d["error"]["field"] is None


class TestPaginatedResponseSchema:
    def test_ok_defaults_true(self) -> None:
        r: PaginatedResponse[int] = PaginatedResponse(data=[1, 2], page_size=2)
        assert r.ok is True

    def test_next_cursor_optional(self) -> None:
        r: PaginatedResponse[str] = PaginatedResponse(
            data=["a"], page_size=10, next_cursor=None
        )
        assert r.next_cursor is None

    def test_with_cursor(self) -> None:
        r: PaginatedResponse[str] = PaginatedResponse(
            data=["a", "b"], page_size=2, next_cursor="eyJpZCI6IDV9"
        )
        assert r.next_cursor == "eyJpZCI6IDV9"

    def test_total_is_optional(self) -> None:
        r: PaginatedResponse[int] = PaginatedResponse(data=[], page_size=20, total=None)
        assert r.total is None


# ---------------------------------------------------------------------------
# AppError hierarchy unit tests
# ---------------------------------------------------------------------------


class TestAppErrorHierarchy:
    def test_app_error_is_exception(self) -> None:
        err = AppError("something went wrong")
        assert isinstance(err, Exception)
        assert err.message == "something went wrong"

    def test_not_found_has_404(self) -> None:
        assert NotFoundError.status_code == 404
        assert NotFoundError.error_code == "not_found"

    def test_conflict_has_409(self) -> None:
        assert ConflictError.status_code == 409

    def test_unauthorized_has_401(self) -> None:
        assert UnauthorizedError.status_code == 401

    def test_forbidden_has_403(self) -> None:
        assert ForbiddenError.status_code == 403

    def test_validation_error_has_422(self) -> None:
        assert ValidationError.status_code == 422

    def test_business_rule_error_has_422(self) -> None:
        assert BusinessRuleError.status_code == 422
        assert BusinessRuleError.error_code == "business_rule_violation"

    def test_optional_field_stored_on_app_error(self) -> None:
        err = NotFoundError("Patient not found", field="patient_id")
        assert err.field == "patient_id"

    def test_all_subclasses_inherit_app_error(self) -> None:
        for cls in (
            NotFoundError,
            ConflictError,
            UnauthorizedError,
            ForbiddenError,
            ValidationError,
            BusinessRuleError,
        ):
            assert issubclass(cls, AppError)


# ---------------------------------------------------------------------------
# Exception handler integration tests
# ---------------------------------------------------------------------------


def _make_error_app() -> FastAPI:
    """Minimal FastAPI app wired with error handlers and error-triggering routes."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/trigger-404")
    def trigger_404():
        raise NotFoundError("Record not found")

    @test_app.get("/trigger-conflict")
    def trigger_conflict():
        raise ConflictError("Already exists")

    @test_app.get("/trigger-business")
    def trigger_business():
        raise BusinessRuleError("Duplicate patient MRN")

    @test_app.get("/trigger-500")
    def trigger_500():
        raise RuntimeError("Something exploded internally")

    @test_app.get("/trigger-http-404")
    def trigger_http_404():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found via HTTP")

    @test_app.post("/trigger-validation")
    def trigger_validation(body: dict[str, int]):
        pass

    return test_app


_err_client = TestClient(_make_error_app(), raise_server_exceptions=False)


class TestErrorHandlerShapes:
    def test_app_not_found_returns_404(self) -> None:
        assert _err_client.get("/trigger-404").status_code == 404

    def test_app_not_found_envelope(self) -> None:
        body = _err_client.get("/trigger-404").json()
        assert body["ok"] is False
        assert body["error"]["code"] == "not_found"
        assert "not found" in body["error"]["message"].lower()

    def test_conflict_returns_409(self) -> None:
        r = _err_client.get("/trigger-conflict")
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "conflict"

    def test_business_rule_returns_422(self) -> None:
        r = _err_client.get("/trigger-business")
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "business_rule_violation"

    def test_unhandled_500_envelope(self) -> None:
        r = _err_client.get("/trigger-500")
        assert r.status_code == 500
        body = r.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "internal_error"
        assert "exploded" not in body["error"]["message"]

    def test_http_exception_404_envelope(self) -> None:
        r = _err_client.get("/trigger-http-404")
        assert r.status_code == 404
        body = r.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "not_found"

    def test_starlette_404_envelope(self) -> None:
        r = _err_client.get("/nonexistent-path")
        assert r.status_code == 404
        assert r.json()["ok"] is False

    def test_request_validation_returns_422(self) -> None:
        r = _err_client.post("/trigger-validation", json={"count": "not-an-int"})
        assert r.status_code == 422
        body = r.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "validation_error"

    def test_error_envelope_keys(self) -> None:
        body = _err_client.get("/trigger-404").json()
        assert set(body.keys()) == {"ok", "error"}
        assert set(body["error"].keys()) == {"code", "message", "field"}

# ---------------------------------------------------------------------------
# Middleware tests
# ---------------------------------------------------------------------------


class TestRequestIDMiddleware:
    def test_response_has_x_request_id(self) -> None:
        r = client.get("/health")
        assert "x-request-id" in r.headers

    def test_request_id_is_valid_uuid(self) -> None:
        r = client.get("/health")
        uuid.UUID(r.headers["x-request-id"])

    def test_client_supplied_request_id_echoed_back(self) -> None:
        custom_id = "my-trace-abc-123"
        r = client.get("/health", headers={"X-Request-ID": custom_id})
        assert r.headers["x-request-id"] == custom_id

    def test_response_has_x_response_time(self) -> None:
        r = client.get("/health")
        assert "x-response-time" in r.headers

    def test_response_time_ends_with_ms(self) -> None:
        r = client.get("/health")
        assert r.headers["x-response-time"].endswith("ms")

    def test_response_time_is_numeric(self) -> None:
        r = client.get("/health")
        float(r.headers["x-response-time"].removesuffix("ms"))

    def test_different_requests_get_different_ids(self) -> None:
        id1 = client.get("/health").headers["x-request-id"]
        id2 = client.get("/health").headers["x-request-id"]
        assert id1 != id2


# ---------------------------------------------------------------------------
# Router registration tests
# ---------------------------------------------------------------------------


class TestRouterRegistration:
    def _paths(self) -> set[str]:
        paths = set()
        for route in app.routes:
            if hasattr(route, "path"):
                paths.add(route.path)
            elif hasattr(route, "routes"):
                for sub in route.routes:
                    if hasattr(sub, "path"):
                        paths.add(sub.path)
            elif hasattr(route, "app") and hasattr(route.app, "routes"):
                for sub in route.app.routes:
                    if hasattr(sub, "path"):
                        paths.add(sub.path)
        return paths

    def test_health_route_registered(self) -> None:
        assert "/health" in self._paths()

    def test_health_ready_registered(self) -> None:
        assert "/health/ready" in self._paths()

    def test_scope_freeze_registered(self) -> None:
        assert "/scope-freeze" in self._paths()

    def test_architecture_registered(self) -> None:
        assert "/architecture" in self._paths()

    def test_domain_glossary_registered(self) -> None:
        assert "/domain-glossary" in self._paths()

    def test_ui_ux_baseline_registered(self) -> None:
        assert "/ui-ux-baseline" in self._paths()

    def test_performance_budget_registered(self) -> None:
        assert "/performance-budget" in self._paths()

    def test_agent_context_baseline_registered(self) -> None:
        assert "/agent-context-baseline" in self._paths()

    def test_no_duplicate_routes(self) -> None:
        routes = []
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                routes.append((route.path, tuple(sorted(route.methods))))
            elif hasattr(route, "routes"):
                for sub in route.routes:
                    if hasattr(sub, "path") and hasattr(sub, "methods"):
                        routes.append((sub.path, tuple(sorted(sub.methods))))
        assert len(routes) == len(set(routes)), f"Duplicate routes: {routes}"

    def test_health_returns_200(self) -> None:
        assert client.get("/health").status_code == 200

    def test_health_status_ok(self) -> None:
        assert client.get("/health").json()["status"] == "ok"

    def test_health_service_field(self) -> None:
        assert client.get("/health").json()["service"] == "api"


# ---------------------------------------------------------------------------
# create_app factory tests
# ---------------------------------------------------------------------------


class TestCreateAppFactory:
    def test_returns_fastapi_instance(self) -> None:
        assert isinstance(create_app(), FastAPI)

    def test_title_set(self) -> None:
        assert create_app().title == "Aarozi Healthcare API"

    def test_version_set(self) -> None:
        assert create_app().version == "0.1.0"

    def test_docs_available_in_development(self) -> None:
        assert create_app().docs_url == "/docs"

    def test_docs_hidden_in_production(self) -> None:
        from unittest.mock import patch
        prod_settings = Settings(_env_file=None, APP_ENV="production")
        with patch("app.main.get_settings", return_value=prod_settings):
            prod_app = create_app()
        assert prod_app.docs_url is None
        assert prod_app.redoc_url is None
        assert prod_app.openapi_url is None

    def test_middleware_stack_non_empty(self) -> None:
        assert len(create_app().user_middleware) > 0

    def test_openapi_available_in_development(self) -> None:
        assert client.get("/openapi.json").status_code == 200

    def test_openapi_lists_health_path(self) -> None:
        paths = client.get("/openapi.json").json()["paths"]
        assert "/health" in paths