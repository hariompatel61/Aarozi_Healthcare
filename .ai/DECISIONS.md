# Architecture Decisions

ADR-001: Use modular monolith first.
Reason: keeps implementation and deployment simple while preserving domain boundaries.

ADR-002: One shared patient identity.
Reason: pathology, billing, reports and blood bank must not create duplicate patient records for the same organization.

ADR-003: Local multi-PC deployment uses a local server.
Reason: four reception PCs need one local source of truth when the internet is unavailable.

ADR-004: Granular permissions use module/resource/action.
Reason: actions like billing.discount or result.approve need independent control.

ADR-005: Report layouts are versioned configuration, not hard-coded pages.
Reason: 100+ templates and custom templates must be maintainable.
