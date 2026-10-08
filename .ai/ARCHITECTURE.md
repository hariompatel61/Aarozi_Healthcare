# Architecture Map - Aarozi Healthcare

## Product model
One login, one unified application shell, one shared patient identity, modules for pathology, billing, blood bank, reports, referral/commission, inventory and administration.

## Client surfaces
Web / Tauri Desktop / Flutter Mobile / Local Analyzer Connector

## Runtime
API + Domain Modules + Background Workers + Optional Local Sync Agent

## Data
PostgreSQL + Redis + Object Storage

## Domain modules
Platform, Identity/RBAC, Patient, Pathology, Billing, Referral, Reporting, Blood Bank, Inventory, Integrations, Sync, Licensing, Notifications.

## Deployment modes
- cloud-only
- local multi-PC
- offline/local
- hybrid local-first + cloud sync

## Local multi-PC architecture
Dedicated local server + PostgreSQL is the source of truth for a site LAN. Desktop clients do not keep independent primary databases.

## Licensing
Offline licenses are signed documents verified locally with a public key. The application never contains a production private signing key. Annual renewal is file-based when the site has no Internet.

## Cloud optionality
Cloud Sync, cloud backup and remote access are entitlements. The offline product does not require cloud endpoints for core workflows. Upgrading to hybrid mode must be possible without reinstalling or recreating local clinical/financial data.

## Performance
Use measured indexes, cache, cursor pagination, virtualization, lazy loading, async report/PDF jobs, local-first reads and horizontal worker/API scaling when cloud load requires it.

## Scaling rule
Do not claim a patient/day number without load-test evidence on defined hardware. The initial offline acceptance target is 5,000 patient registrations/day with four concurrent LAN clients; the cloud architecture should be validated independently at its target request rate.
