# P03-07 - Order Workflow

## Objective
Implement order and order-item state transitions.

## Dependencies
- P03-06

## Context files
- .ai/DOMAIN_GLOSSARY.yml
- .ai/STATE_MACHINES.md
- .ai/PERFORMANCE_BUDGET.md

## Implementation prompt
`	ext
Implement P03-07: Order Workflow for Aarozi Healthcare.

Read the task file and only the listed context files before coding. Inspect only the smallest relevant code surface.
Do not redesign unrelated modules. Follow the canonical architecture, schema, RBAC and performance rules.
Implement the objective completely, add the required tests, and stop when this task is green.

Specific objective:
Implement order and order-item state transitions.

Acceptance rules:
- multi-tenant safe
- auditable when state/data changes are sensitive
- server-side authorization where applicable
- no unbounded queries
- no hidden dependency on internet for approved offline flows
- no unrelated refactor
`

## Test / verification
1. Run:
- python -m pytest apps/api/tests/test_order_workflow.py -q
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
- Added Order and OrderItem models with multi-tenant foreign keys, composite indexes, and status tracking in pps/api/app/models/pathology.py.
- Exported Order and OrderItem via pps/api/app/models/__init__.py.
- Created Alembic database migration 20241013_05_orders_and_order_items.py with indexes and unique constraints on (tenant_id, order_no).
- Implemented core order workflow service in pps/api/app/pathology/order_workflow.py:
  - generate_order_no: scoped sequential order numbers (ORD-YYYYMMDD-XXXX).
  - create_order: supports explicit line items or hierarchical expansion from tests, profiles, and packages.
  - get_order, list_orders: tenant-isolated queries with bounded pagination.
  - 	ransition_order_status & 	ransition_order_item_status: state machine validation with cancellation reasons and roll-up state aggregation (draft -> placed -> sample_collected -> in_process -> partial_completed -> completed).
- Added unit test suite pps/api/tests/test_order_workflow.py (7 tests covering creation, packages/profiles expansion, transition rules, cancellation reasons, and multi-tenant isolation - all green).
