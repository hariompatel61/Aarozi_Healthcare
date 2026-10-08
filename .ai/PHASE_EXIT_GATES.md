# Phase Exit Gates

## P00 - Product Control Plane
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P01 - Repository and Local Development
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P02 - Database, Tenant and RBAC
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P03 - Patient, Registration and Order
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P04 - Billing and Referral
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P05 - Pathology Result Engine
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P06 - Reporting and 100+ Templates
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P07 - Blood Bank
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P08 - Analyzer and External Integrations
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P09 - Offline, Local Server, Sync and Licensing
Exit only when:
- all P09-01 through P09-20 tasks are green
- core workflows work with Internet fully disconnected
- four or more LAN clients use one local PostgreSQL source of truth without duplicate identifiers
- signed offline activation and renewal work by file transfer only
- license expiry does not delete/corrupt data and clock rollback is detected
- cloud entitlement can be enabled later without reinstalling the local system
- sync is batch-based, idempotent, checkpointed and resumable
- local backup restore has a passing recovery drill
- 5,000-patient/day synthetic acceptance evidence exists on defined hardware
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P10 - Ultra-Fast Web UX
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P11 - Desktop and Mobile
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P12 - Security, QA, Performance and Observability
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated

## P13 - Pilot and Production
Exit only when:
- all tasks in the phase are green
- no task-specific test remains failing
- database migrations are reproducible where applicable
- audit/RBAC requirements are covered where applicable
- performance budget has no unexplained regression
- next-phase dependency files are updated
