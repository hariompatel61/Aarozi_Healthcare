"""P00-04: frozen UI/UX conventions, not a UI or authorization implementation.

Future clients must implement these conventions. Navigation describes stable
logical destinations, not currently available routes or granted permissions.
This contract contains no tenant, user, branch or patient data.
"""

from __future__ import annotations

from typing import TypedDict


class Density(TypedDict):
    font_size_px: int
    control_height_px: int
    table_row_height_px: int
    spacing_unit_px: int


class NavigationItem(TypedDict):
    module: str
    label: str
    entities: tuple[str, ...]


class KeyboardPattern(TypedDict):
    keys: str
    scope: str
    behavior: str


class UIState(TypedDict):
    announcement: str
    behavior: str


SHELL_REGIONS: tuple[str, ...] = (
    "skip_link",
    "header",
    "primary_navigation",
    "main",
    "status_region",
)

SHELL_RULES: tuple[str, ...] = (
    "Use one application shell and one shared patient identity across modules.",
    "Header shows tenant, branch and user labels derived from authenticated server context.",
    "Never put patient details in the persistent shell, page title or navigation history.",
    "Provide one main landmark and page heading; the skip link focuses main content.",
    "Keep navigation order stable; indicate the current destination with aria-current.",
    "On narrow screens collapse navigation behind a labelled button; preserve content and keyboard access.",
    "After navigation focus the page heading; closing navigation restores focus to its trigger.",
    "Show local-server connectivity separately from optional cloud-sync availability.",
)

DEFAULT_DENSITY: str = "compact"
DENSITIES: dict[str, Density] = {
    "compact": {
        "font_size_px": 14,
        "control_height_px": 32,
        "table_row_height_px": 32,
        "spacing_unit_px": 4,
    },
    "comfortable": {
        "font_size_px": 16,
        "control_height_px": 44,
        "table_row_height_px": 44,
        "spacing_unit_px": 8,
    },
}
DENSITY_RULES: tuple[str, ...] = (
    "Default operational screens to compact; offer comfortable density for touch use.",
    "Density affects presentation only and must never change permissions or data.",
    "Use system fonts and locally bundled assets; do not require remote fonts or CDNs.",
    "Support 200% text zoom and reflow; contain wide-table scrolling within the table region.",
    "Use visible focus indicators, labelled controls and text alongside status colors.",
    "Meet WCAG AA contrast: 4.5:1 normal text, 3:1 large text and UI indicators.",
)

NAVIGATION: tuple[NavigationItem, ...] = (
    {"module": "patient", "label": "Patient", "entities": ("patient",)},
    {
        "module": "pathology",
        "label": "Pathology",
        "entities": ("order", "sample", "result"),
    },
    {"module": "billing", "label": "Billing", "entities": ("invoice", "payment")},
    {"module": "reporting", "label": "Reporting", "entities": ("report",)},
    {
        "module": "blood_bank",
        "label": "Blood bank",
        "entities": ("donor", "donation", "blood_unit", "cross_match"),
    },
    {
        "module": "platform",
        "label": "Administration",
        "entities": ("branch", "user", "role", "permission", "license", "backup"),
    },
)

KEYBOARD_PATTERNS: tuple[KeyboardPattern, ...] = (
    {
        "keys": "Tab / Shift+Tab",
        "scope": "page",
        "behavior": "Move through enabled controls in DOM order; never use positive tabindex.",
    },
    {
        "keys": "Enter",
        "scope": "focused_link_or_button",
        "behavior": "Activate the focused control, never an unfocused clinical or financial action.",
    },
    {
        "keys": "Space",
        "scope": "focused_button_or_checkbox",
        "behavior": "Use native activation or toggle behavior; do not override text entry.",
    },
    {
        "keys": "Escape",
        "scope": "dismissible_overlay",
        "behavior": "Close the topmost overlay and restore trigger focus; confirm before discarding unsaved edits.",
    },
    {
        "keys": "Arrow keys / Home / End",
        "scope": "composite_widget",
        "behavior": "Follow the widget ARIA pattern; do not intercept page scrolling or text editing.",
    },
)
KEYBOARD_RULES: tuple[str, ...] = (
    "Every action has a labelled, keyboard-reachable control; shortcuts are optional enhancements.",
    "Do not register global single-character shortcuts or override browser and assistive shortcuts.",
    "Dialogs have accessible names, initial focus, contained tab order and focus restoration.",
    "Enter in multiline input inserts a newline; never implicitly approve, release, pay or delete.",
    "Sensitive actions require explicit confirmation, server authorization and durable audit history.",
    "Preserve entered values on validation failure; focus an error summary linked to invalid fields.",
)

UI_STATES: dict[str, UIState] = {
    "loading": {
        "announcement": "polite",
        "behavior": "Mark the affected region aria-busy, show progress and prevent duplicate submissions.",
    },
    "empty": {
        "announcement": "polite",
        "behavior": "Distinguish no records from no filter matches; offer only authorized next actions.",
    },
    "error": {
        "announcement": "assertive",
        "behavior": "Show a safe actionable message, preserve edits and offer retry only when safe.",
    },
    "permission_denied": {
        "announcement": "assertive",
        "behavior": "Fail closed without protected data; explain restricted access and offer safe navigation.",
    },
    "ready": {
        "announcement": "polite",
        "behavior": "Announce operation outcomes without patient details; do not steal focus on background updates.",
    },
}

# These are requirements for consumers, not substitutes for backend enforcement.
SAFETY_RULES: dict[str, str] = {
    "identity_source": "authenticated_server_context",
    "patient_scope": "server_validated_tenant_branch_and_permission",
    "authorization": "server_side_on_every_protected_read_and_write",
    "navigation_visibility": "server_authorized_and_module_enabled",
    "unknown_permissions": "deny_until_resolved",
    "direct_navigation": "same_server_authorization_as_menu_navigation",
    "context_change": "clear_scoped_data_and_reauthorize_before_rendering",
    "sensitive_write": "explicit_confirmation_transaction_and_durable_audit",
    "retryable_write": "idempotent_without_duplicate_side_effects",
    "logging": "no_secrets_tokens_or_patient_payloads",
    "list_queries": "bounded_server_side_pagination_and_filtering",
    "local_source_of_truth": "shared_local_server",
    "local_server_unavailable": "preserve_edits_block_writes_never_claim_success",
    "core_offline_flows": "no_internet_or_cloud_dependency",
    "cloud_features": "optional_and_entitlement_gated",
    "license_expiry": "never_delete_or_corrupt_clinical_or_financial_data",
}


class UIUXBaseline(TypedDict):
    version: int
    shell_regions: tuple[str, ...]
    shell_rules: tuple[str, ...]
    default_density: str
    densities: dict[str, Density]
    density_rules: tuple[str, ...]
    navigation: tuple[NavigationItem, ...]
    keyboard_patterns: tuple[KeyboardPattern, ...]
    keyboard_rules: tuple[str, ...]
    states: dict[str, UIState]
    safety_rules: dict[str, str]


UI_UX_BASELINE: UIUXBaseline = {
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
