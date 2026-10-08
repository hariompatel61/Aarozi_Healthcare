# P09-16 - Offline 5,000 Patient Multi-PC Acceptance

## Objective
Validate the offline product with a realistic 5,000-patient day and at least four simultaneous LAN clients.

## Dependencies
P09-15.

## Context files
- `docs/OFFLINE_ACCEPTANCE_TESTS.md`
- `docs/LOCAL_SERVER_OPERATIONS.md`
- `.ai/PERFORMANCE_BUDGET.md`

## Implementation prompt
Create a deterministic synthetic workload generator and acceptance suite for 5,000 patients/day on a local server. Include patient registration, orders, billing, samples, results, reports and audit events. Test at least four concurrent clients and capture p50/p95, DB resource usage and storage growth.

## Test / verification
Run the workload with Internet physically disconnected. Confirm no cloud dependency and no data loss. Record evidence in the load-test report.

## Done criteria
The offline capacity target is measured on defined hardware rather than assumed.
