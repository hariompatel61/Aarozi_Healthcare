# Aarozi Healthcare - AI Agent Rules

## Non-negotiable

1. Read `.ai/AGENT_IMPLEMENTATION_PROTOCOL.md` before coding.
2. Work on exactly ONE task file at a time.
3. Read only the context files named by the task.
4. Do not redesign architecture unless the task explicitly allows it.
5. Do not introduce microservices during MVP implementation.
6. Keep clinical/financial facts relational and transactional.
7. Never trust tenant_id, user_id, patient_id or branch_id supplied by the browser when server context can derive it.
8. Never log secrets, passwords, tokens or patient payloads unnecessarily.
9. Add or update tests in the same task.
10. Run task-level tests before finishing.
11. Do not modify unrelated files.
12. Stop after the task acceptance criteria are green.
13. Never ship production signing private keys inside the client application.
14. Offline core workflows must not require cloud connectivity.
15. Cloud features must be entitlement-gated and optional.
16. License expiry must never delete or corrupt clinical/financial data.

## Code style

- TypeScript strict mode.
- Python typing + linting.
- Small modules with clear boundaries.
- Prefer explicit names over clever abstractions.
- Avoid N+1 queries.
- Paginate unbounded lists.
- Use database constraints for invariants.
- Use idempotency for retryable writes.
- Treat clinical/financial audit records as durable history.

## Performance

- Keep initial client payload small.
- Lazy-load heavy modules.
- Prefer server-side pagination and filtering.
- Keep report/PDF/export jobs asynchronous.
- Measure before optimizing.
- In offline deployments, keep the local server as the shared LAN source of truth.
- Do not make remote/cloud availability a dependency of local registration, billing, sample, result, report or blood-bank operations.

## Offline licensing

- Verify signed licenses locally.
- Key IDs and public verification keys are safe to distribute; private signing keys are not.
- Activation and renewal request files must contain no patient records.
- Clock rollback must never silently extend validity.

## Ponytail — Lazy Senior Developer Mode 🐴

- "The best code is the code you never wrote."
- **YAGNI**: Build only what is needed right now.
- **Zero Dependencies**: Native APIs and standard libraries first. Always.
- **Delete Code**: The best PR removes more lines than it adds.
- **Simplicity > Cleverness**: Write boring, readable, maintainable code.
