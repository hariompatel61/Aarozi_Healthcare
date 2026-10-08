# Deployment

## Cloud
Containerized API/web/worker + PostgreSQL + Redis + object storage + observability.

## Local offline
A local Windows server installation hosts API, PostgreSQL and workers. Desktop clients connect over LAN. No cloud endpoint is required for core workflows.

## Hybrid
Local-first writes + durable sync queue + resumable batch transfer to cloud. Cloud features are enabled only after the appropriate entitlement/license is installed.

## Never-online sites
Activation and renewal are file based. The local installation exports an activation/renewal request; an Aarozi licensing operator returns a signed license file; the customer imports it locally.

## Operational requirements
- health checks
- structured logs
- metrics
- audit logs
- backup/restore automation
- license status
- sync status when enabled
- printer/barcode/analyzer diagnostics
- clear service recovery runbook

## Installation rule
For multi-PC offline sites, install one local server and multiple desktop clients. Do not create independent primary databases per workstation.
