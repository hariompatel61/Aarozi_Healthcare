"""Tests for P00-01 Scope Freeze."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestScopeFreeze:
    """Verify the scope freeze endpoint returns valid frozen scope data."""

    def test_scope_freeze_returns_200(self) -> None:
        r = client.get("/scope-freeze")
        assert r.status_code == 200

    def test_scope_freeze_status_is_frozen(self) -> None:
        data = client.get("/scope-freeze").json()
        assert data["status"] == "FROZEN"

    def test_scope_freeze_has_boundaries(self) -> None:
        data = client.get("/scope-freeze").json()
        boundaries = data["boundaries"]
        assert "mvp" in boundaries
        assert "v1" in boundaries
        assert "v2" in boundaries

    def test_mvp_boundary_modules(self) -> None:
        data = client.get("/scope-freeze").json()
        mvp = data["boundaries"]["mvp"]
        expected_modules = [
            "identity_rbac",
            "patient_management",
            "registration_orders",
            "pathology_lims",
            "billing_referral",
            "report_engine",
        ]
        assert mvp["modules"] == expected_modules

    def test_mvp_deployment_modes(self) -> None:
        data = client.get("/scope-freeze").json()
        mvp = data["boundaries"]["mvp"]
        assert "cloud" in mvp["deployment_modes"]
        assert "local_multi_pc" in mvp["deployment_modes"]

    def test_v1_adds_blood_bank_and_offline(self) -> None:
        data = client.get("/scope-freeze").json()
        v1 = data["boundaries"]["v1"]
        assert "blood_bank" in v1["modules"]
        assert "hybrid_offline" in v1["modules"]
        assert "offline" in v1["deployment_modes"]
        assert "hybrid" in v1["deployment_modes"]

    def test_v2_includes_hardening_and_launch(self) -> None:
        data = client.get("/scope-freeze").json()
        v2 = data["boundaries"]["v2"]
        assert "hardening" in v2["modules"]
        assert "launch" in v2["modules"]

    def test_assumptions_and_open_decisions_counts(self) -> None:
        data = client.get("/scope-freeze").json()
        assert data["assumptions_count"] == 10
        assert data["open_decisions_count"] == 7

    def test_scope_freeze_has_document_version(self) -> None:
        data = client.get("/scope-freeze").json()
        assert data["document_version"] == "1.0.0"

    def test_scope_freeze_has_freeze_date(self) -> None:
        data = client.get("/scope-freeze").json()
        assert data["freeze_date"] == "2026-10-08"

    def test_blood_bank_not_in_mvp(self) -> None:
        """Blood bank is V1 scope, must not leak into MVP."""
        data = client.get("/scope-freeze").json()
        mvp_modules = data["boundaries"]["mvp"]["modules"]
        assert "blood_bank" not in mvp_modules

    def test_offline_mode_not_in_mvp(self) -> None:
        """Offline deployment mode is V1 scope, not MVP."""
        data = client.get("/scope-freeze").json()
        mvp_modes = data["boundaries"]["mvp"]["deployment_modes"]
        assert "offline" not in mvp_modes
