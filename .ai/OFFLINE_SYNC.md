# Offline / Local / Hybrid Architecture

## Commercial principle
Aarozi Healthcare is offline-first. Core clinical and financial workflows must work without Internet. Cloud Sync is optional and enabled only by the subscribed entitlement.

## Modes
1. `OFFLINE_LOCAL`: local server + LAN desktop clients, no cloud dependency.
2. `HYBRID_SYNC`: local-first writes; durable sync queue transfers approved changes to cloud.
3. `CLOUD`: cloud-first deployment when selected.

## Recommended 4-PC site
Use one local server on the site LAN rather than four disconnected databases.

```text
PC-1 ─┐
PC-2 ─┤
PC-3 ─┼──> Aarozi Local Server ──> PostgreSQL
PC-4 ─┘             |
              Optional Sync Agent
                     |
                   Cloud
```

## Offline behavior
The following must not require cloud calls:
- patient registration/search
- order creation
- billing, discounts, payments and receipts
- sample workflows
- barcode/QR generation
- result entry/verification/approval
- report rendering/printing
- blood-bank operations
- analyzer workflows supported by local connectors
- audit logging
- import/export
- local backup/restore

## Syncable record
Each syncable fact should carry:
- stable id
- tenant_id
- branch_id
- version
- origin_device_id
- created_at
- updated_at
- sync stream / sequence

## Batch sync
Use durable checkpoints. Sync in batches. Each batch has an idempotency key and is acknowledged only after committed application. Resume from the last acknowledged sequence.

## Large files
PDFs, scanned documents and other objects must sync independently from database facts and use resumable object uploads where supported.

## Conflict rule
Never use blind last-write-wins for clinical results, financial facts, blood inventory or license state. Use domain-specific resolution and preserve both versions where needed.

## Failure rule
Cloud outage or sync failure must never block local operations. Failed events remain durable and visible in a local sync-status queue.
