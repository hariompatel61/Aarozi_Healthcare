# P09-17 - Offline Backup and Restore

## Objective
Provide encrypted local backup, restore validation and operator-safe recovery.

## Dependencies
P09-16.

## Context files
- `docs/LOCAL_SERVER_OPERATIONS.md`
- `docs/OFFLINE_ACCEPTANCE_TESTS.md`
- `.ai/SECURITY_RULES.md`

## Implementation prompt
Implement manual and scheduled local backups, encrypted backup archives, restore preflight validation, and a safe restore wizard. Backup must not include secrets in plain text. Add integrity checks and a restore test command.

## Test / verification
Create backup, corrupt one copy, reject it, restore a valid backup into a disposable environment, verify patient/billing/report/blood-bank counts and checksums.

## Done criteria
Backup is recoverable and restore is routinely testable.
