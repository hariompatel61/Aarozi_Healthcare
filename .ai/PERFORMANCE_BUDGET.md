# Aarozi Healthcare Performance Budget

## UX targets
- First meaningful interaction on common desktop screens: target <= 1.5 s on a warm production path.
- Common search/list interactions: target <= 300 ms perceived response after cache/local filtering where practical.
- Avoid blocking the main thread with PDF generation, exports or large table transforms.
- Heavy modules must be lazy-loaded.

## API targets
- Ordinary CRUD/query p95 target < 500 ms under expected load.
- Long-running jobs are asynchronous.
- High-volume feeds use cursor pagination.

## Database
- Every operational queue has a supporting composite index.
- Search uses normalized indexed fields; avoid leading-wildcard scans on large tables.
- Use `EXPLAIN (ANALYZE, BUFFERS)` for slow queries.
- Avoid ORM-generated N+1 queries.

## Frontend
- Route-level code splitting.
- Virtualized tables for large queues.
- Debounced search.
- Cache stable masters (tests, doctors, departments) with TTL/invalidation.
- Preserve form state during navigation where workflow requires it.

## Offline
- Reads should use local cache/local DB first for offline-supported workflows.
- Sync queues must be append-oriented and retryable.
- Conflicts must be visible and resolved by domain rules, not silent overwrite.


## Offline commercial acceptance
- Initial validation target: 5,000 patient registrations/day with at least four concurrent LAN clients on defined local-server hardware.
- Core local workflows must remain usable with Internet physically disconnected.
- Measure patient search, order creation, billing, result save and report queue p50/p95.
- Report/PDF generation must remain asynchronous and must not block registration/billing.
- Sync throughput must be benchmarked separately from local transaction latency.
