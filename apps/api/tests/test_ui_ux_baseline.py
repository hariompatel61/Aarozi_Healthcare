"""P00-04 contract tests; no claim of rendered UI or runtime RBAC coverage."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from contracts.architecture import DOMAIN_MODULES
from contracts.domain_glossary import CANONICAL_ENTITIES
from contracts.ui_ux_baseline import (
    DEFAULT_DENSITY,
    DENSITIES,
    DENSITY_RULES,
    KEYBOARD_PATTERNS,
    KEYBOARD_RULES,
    NAVIGATION,
    SAFETY_RULES,
    SHELL_REGIONS,
    SHELL_RULES,
    UI_STATES,
    UI_UX_BASELINE,
)


def test_composite_export_is_complete_and_serializable() -> None:
    assert UI_UX_BASELINE == {
        "version": 1,
        "shell_regions": SHELL_REGIONS,
        "shell_rules": SHELL_RULES,
        "default_density": DEFAULT_DENSITY,
        "densities": DENSITIES,
        "density_rules": DENSITY_RULES,
        "navigation": NAVIGATION,
        "keyboard_patterns": KEYBOARD_PATTERNS,
        "keyboard_rules": KEYBOARD_RULES,
        "states": UI_STATES,
        "safety_rules": SAFETY_RULES,
    }
    decoded = json.loads(json.dumps(UI_UX_BASELINE))
    assert decoded["version"] == 1
    assert decoded["navigation"][0]["entities"] == ["patient"]


def test_shell_landmarks_and_order_are_frozen() -> None:
    assert SHELL_REGIONS == (
        "skip_link", "header", "primary_navigation", "main", "status_region",
    )
    assert len(SHELL_REGIONS) == len(set(SHELL_REGIONS))


def test_density_values_are_frozen() -> None:
    assert DEFAULT_DENSITY == "compact"
    assert DENSITIES == {
        "compact": {
            "font_size_px": 14, "control_height_px": 32,
            "table_row_height_px": 32, "spacing_unit_px": 4,
        },
        "comfortable": {
            "font_size_px": 16, "control_height_px": 44,
            "table_row_height_px": 44, "spacing_unit_px": 8,
        },
    }


def test_navigation_order_matches_existing_domain_modules() -> None:
    modules = [item["module"] for item in NAVIGATION]
    assert modules == [
        "patient", "pathology", "billing", "reporting", "blood_bank", "platform",
    ]
    assert len(modules) == len(set(modules))
    assert set(modules) <= set(DOMAIN_MODULES)
    assert all(item["label"].strip() for item in NAVIGATION)


def test_navigation_uses_canonical_entities_and_one_patient_destination() -> None:
    entities = [entity for item in NAVIGATION for entity in item["entities"]]
    assert set(entities) <= set(CANONICAL_ENTITIES)
    assert len(entities) == len(set(entities))
    assert entities.count("patient") == 1
    assert {"order", "sample", "result", "invoice", "report", "blood_unit"} <= set(entities)
    assert all(item["entities"] for item in NAVIGATION)


def test_keyboard_patterns_use_scoped_native_behaviors() -> None:
    assert [(item["keys"], item["scope"]) for item in KEYBOARD_PATTERNS] == [
        ("Tab / Shift+Tab", "page"),
        ("Enter", "focused_link_or_button"),
        ("Space", "focused_button_or_checkbox"),
        ("Escape", "dismissible_overlay"),
        ("Arrow keys / Home / End", "composite_widget"),
    ]
    assert all(item["behavior"].strip() for item in KEYBOARD_PATTERNS)
    assert "never use positive tabindex" in KEYBOARD_PATTERNS[0]["behavior"]
    assert "never an unfocused clinical or financial action" in KEYBOARD_PATTERNS[1]["behavior"]
    assert "confirm before discarding unsaved edits" in KEYBOARD_PATTERNS[3]["behavior"]


def test_required_ui_states_are_complete() -> None:
    assert set(UI_STATES) == {"loading", "empty", "error", "permission_denied", "ready"}


@pytest.mark.parametrize(
    ("state", "announcement", "required_behavior"),
    [
        ("loading", "polite", "prevent duplicate submissions"),
        ("empty", "polite", "only authorized next actions"),
        ("error", "assertive", "preserve edits"),
        ("permission_denied", "assertive", "without protected data"),
        ("ready", "polite", "without patient details"),
    ],
)
def test_state_accessibility_and_safety(
    state: str, announcement: str, required_behavior: str,
) -> None:
    assert UI_STATES[state]["announcement"] == announcement
    assert required_behavior in UI_STATES[state]["behavior"]


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ("identity_source", "authenticated_server_context"),
        ("patient_scope", "server_validated_tenant_branch_and_permission"),
        ("authorization", "server_side_on_every_protected_read_and_write"),
        ("navigation_visibility", "server_authorized_and_module_enabled"),
        ("unknown_permissions", "deny_until_resolved"),
        ("direct_navigation", "same_server_authorization_as_menu_navigation"),
        ("context_change", "clear_scoped_data_and_reauthorize_before_rendering"),
        ("sensitive_write", "explicit_confirmation_transaction_and_durable_audit"),
        ("retryable_write", "idempotent_without_duplicate_side_effects"),
        ("logging", "no_secrets_tokens_or_patient_payloads"),
        ("list_queries", "bounded_server_side_pagination_and_filtering"),
        ("local_source_of_truth", "shared_local_server"),
        ("local_server_unavailable", "preserve_edits_block_writes_never_claim_success"),
        ("core_offline_flows", "no_internet_or_cloud_dependency"),
        ("cloud_features", "optional_and_entitlement_gated"),
        ("license_expiry", "never_delete_or_corrupt_clinical_or_financial_data"),
    ],
)
def test_security_offline_and_performance_requirements(rule: str, expected: str) -> None:
    assert SAFETY_RULES[rule] == expected


@pytest.mark.parametrize(
    ("rules", "required_text"),
    [
        (SHELL_RULES, "authenticated server context"),
        (SHELL_RULES, "skip link focuses main content"),
        (SHELL_RULES, "preserve content and keyboard access"),
        (DENSITY_RULES, "200% text zoom"),
        (DENSITY_RULES, "locally bundled assets"),
        (DENSITY_RULES, "WCAG AA contrast"),
        (KEYBOARD_RULES, "shortcuts are optional enhancements"),
        (KEYBOARD_RULES, "contained tab order and focus restoration"),
        (KEYBOARD_RULES, "never implicitly approve, release, pay or delete"),
        (KEYBOARD_RULES, "error summary linked to invalid fields"),
    ],
)
def test_accessibility_and_operational_guards(
    rules: tuple[str, ...], required_text: str,
) -> None:
    assert any(required_text in rule for rule in rules)
