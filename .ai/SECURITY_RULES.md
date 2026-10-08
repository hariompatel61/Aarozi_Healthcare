# Security Rules

- Tenant context comes from authenticated server context.
- Authorization is evaluated server-side for every protected endpoint.
- Branch/department scope must be enforced in queries, not only UI.
- Patient identifiers are treated as sensitive.
- Result amendments require reason and prior-version preservation.
- Financial changes must be auditable.
- File access is private-by-default with temporary signed access when needed.
- Secrets belong in environment/secret management, never source control.
- Bulk export is explicit and logged.
- Admin/support impersonation is time-limited and logged.
- Use secure password hashing and revocable sessions.
- Do not expose internal primary keys as authorization mechanisms.
