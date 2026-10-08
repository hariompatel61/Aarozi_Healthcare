# Database migration order

Run SQL files in numeric order from `001_` through the latest file.

Production migrations should eventually be managed by Alembic; these SQL files are the canonical schema intent/reference. Do not run destructive migrations automatically in production.

Before production:
- test forward migration on a clean DB
- test upgrade from previous release
- test rollback/forward recovery strategy
- verify indexes with EXPLAIN
- verify backup restore
