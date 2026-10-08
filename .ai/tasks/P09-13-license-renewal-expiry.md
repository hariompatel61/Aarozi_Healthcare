# P09-13 - License Renewal, Expiry and Clock Rollback

## Objective
Implement annual renewal, grace/restricted state and practical clock rollback detection.

## Dependencies
P09-12.

## Context files
- `.ai/OFFLINE_LICENSE_MODEL.md`
- `docs/RENEWAL_AND_ACTIVATION.md`
- `database/012_commercial_offline_license.sql`

## Implementation prompt
Implement license lifecycle states: active, grace, expired/restricted, revoked, recovery-review. Add 30/15/7/1-day reminders, immutable local audit events, durable last-trusted-time metadata and clock rollback detection. Never delete data at expiry. Keep renewal file import offline.

## Test / verification
Use deterministic time fixtures. Verify grace boundaries, expired behavior, rollback detection and renewal restoration.

## Done criteria
Expiry and renewal are predictable, testable and data-safe.
