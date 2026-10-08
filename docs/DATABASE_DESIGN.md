# Aarozi Healthcare - Database Design

## Rules
- PostgreSQL is authoritative cloud DB.
- Tenant-owned data carries tenant_id.
- UUID/ULID public identifiers.
- timestamptz stored in UTC.
- strong FKs, unique constraints and check constraints.
- append-only audit and immutable financial/clinical history where applicable.
- JSONB only for configuration, templates and external payloads; core facts stay relational.

See `database/` for starter SQL migrations.
