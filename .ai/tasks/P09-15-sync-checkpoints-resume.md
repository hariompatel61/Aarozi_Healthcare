# P09-15 - Resumable Batch Sync

## Objective
Make local-to-cloud synchronization batch-based, idempotent and resumable.

## Dependencies
P09-14.

## Context files
- `.ai/OFFLINE_SYNC.md`
- `.ai/CLOUD_OPTIONALITY.md`
- `database/012_commercial_offline_license.sql`
- `.ai/API_CONTRACT_RULES.md`

## Implementation prompt
Implement durable sync checkpoints, batch acknowledgements, retry with backoff, idempotency keys and resume from the last acknowledged sequence. Large files must sync independently from core database facts. A sync failure must never block local operations.

## Test / verification
Interrupt the network at random batch boundaries, resume, verify exact-once logical application and no duplicate invoices/results.

## Done criteria
Sync can stop and resume without reprocessing committed facts incorrectly.
