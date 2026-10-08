# P10-07 - UX Performance Gate

## Objective
Measure common workflows and fix regressions against performance budget.

## Dependencies
- P10-06

## Context files
- `.ai/UI_UX_SYSTEM.md`
- `.ai/PERFORMANCE_BUDGET.md`
- `.ai/ARCHITECTURE.md`

## Implementation prompt
```text
Implement P10-07: UX Performance Gate for Aarozi Healthcare.

Read the task file and only the listed context files before coding. Inspect only the smallest relevant code surface.
Do not redesign unrelated modules. Follow the canonical architecture, schema, RBAC and performance rules.
Implement the objective completely, add the required tests, and stop when this task is green.

Specific objective:
Measure common workflows and fix regressions against performance budget.

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
- `npm --prefix apps/web run build`
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
