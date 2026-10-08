# P07-03 - Donation

## Objective
Implement donation records and component generation.

## Dependencies
- P07-02

## Context files
- `.ai/DOMAIN_GLOSSARY.yml`
- `.ai/STATE_MACHINES.md`
- `docs/BLOOD_BANK.md`
- `.ai/SECURITY_RULES.md`

## Implementation prompt
```text
Implement P07-03: Donation for Aarozi Healthcare.

Read the task file and only the listed context files before coding. Inspect only the smallest relevant code surface.
Do not redesign unrelated modules. Follow the canonical architecture, schema, RBAC and performance rules.
Implement the objective completely, add the required tests, and stop when this task is green.

Specific objective:
Implement donation records and component generation.

Acceptance rules:
- multi-tenant safe
- auditable when state/data changes are sensitive
- server-side authorization where applicable
- no unbounded queries
- no hidden dependency on internet for approved offline flows
- no unrelated refactor
```

## Test / verification
1. Run:
- `python -m pytest apps/api/tests -q`
2. Add focused unit/API/E2E tests appropriate to the task.
3. For DB changes, run migration up/down or rollback verification where supported.
4. For UI changes, verify loading, empty, error, keyboard and permission states.
5. For clinical/financial state changes, verify positive and negative paths plus audit/version behaviour.

## Done criteria
- Task objective implemented.
- Tests added or updated.
- No task-related failing tests.
- No secrets committed.
- No unrelated files changed.
- Performance constraints from context are respected.

## Agent output
Return only:
- changed files
- tests run
- result
- follow-up (if any)
