# P09-20 - Commercial Offline Release Gate

## Objective
Package the offline-only product as a sellable annual license tier.

## Dependencies
P09-19.

## Context files
- `docs/COMMERCIAL_OFFLINE_MODEL.md`
- `docs/RENEWAL_AND_ACTIVATION.md`
- `docs/OFFLINE_ACCEPTANCE_TESTS.md`
- `.ai/PHASE_EXIT_GATES.md`

## Implementation prompt
Create the release checklist and product configuration for the OFFLINE_LOCAL plan. Verify licensing, local install, four-PC operation, backup/restore, expiry/renewal, performance acceptance and cloud-disabled behavior. Do not enable cloud by default.

## Test / verification
Run the full offline acceptance suite with Internet blocked and use a signed test license. Verify cloud endpoints are not required for core workflows.

## Done criteria
The offline commercial package passes its release gate and can be handed to a pilot lab.
