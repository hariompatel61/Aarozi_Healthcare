# Cloud Optionality Rules

1. Core clinical/financial workflows must not call cloud endpoints in OFFLINE_LOCAL mode.
2. Cloud modules are feature-gated by entitlement, not by scattered boolean checks.
3. Offline mode must not show broken cloud UI. Hide or clearly mark cloud-only actions.
4. Switching OFFLINE_LOCAL -> HYBRID_SYNC is an in-place upgrade of the same local dataset.
5. Initial sync must be resumable and idempotent.
6. Existing local identifiers remain stable during cloud onboarding; cloud IDs are mapped explicitly.
7. Disable or revoke cloud access without removing local data.
8. Cloud sync failures must never block local patient registration, billing, sample or result workflows.
9. Every sync batch receives a durable checkpoint and retry state.
