# API Contract Rules

- Base path: `/api/v1`
- JSON for ordinary CRUD.
- Cursor pagination for high-volume feeds.
- Idempotency-Key for retryable writes where applicable.
- Consistent error shape: `{code, message, field_errors, correlation_id}`.
- Tenant and authorization derived server-side.
- Long jobs return job id and poll/status endpoint or push event.
- Use explicit versioning for breaking contract changes.
- Do not expose raw SQL errors.
