# Aarozi Healthcare

Unified diagnostic laboratory + pathology + billing + blood bank SaaS with an **offline-first commercial model**.

## Core product promise
- One application
- One login
- One shared patient record
- Pathology + billing + blood bank + reports + referral/commission in the same workspace
- Multiple users and multiple PCs work simultaneously
- Annual offline/local license works without Internet
- Cloud Sync is an optional paid plan
- Same installation can be upgraded from offline-only to hybrid sync
- Web + Windows desktop + mobile + analyzer connector

## Build kit
This repository is a coding-ready foundation and AI task control plane. It is not a finished production LIS. Build one task at a time from `.ai/tasks/`.

## First task
`.ai/tasks/P00-01-scope-freeze.md`

## Offline commercial tasks
The additional offline/licensing hardening sequence is:
- `.ai/tasks/P09-11-offline-license-signing.md`
- `.ai/tasks/P09-12-offline-activation-request.md`
- `.ai/tasks/P09-13-license-renewal-expiry.md`
- `.ai/tasks/P09-14-cloud-optional-entitlement.md`
- `.ai/tasks/P09-15-sync-checkpoints-resume.md`
- `.ai/tasks/P09-16-offline-5k-multipc-acceptance.md`
- `.ai/tasks/P09-17-local-backup-restore.md`
- `.ai/tasks/P09-18-local-server-installer.md`
- `.ai/tasks/P09-19-local-print-barcode-analyzer.md`
- `.ai/tasks/P09-20-commercial-offline-release.md`

## Key documents
- `docs/COMMERCIAL_OFFLINE_MODEL.md`
- `docs/RENEWAL_AND_ACTIVATION.md`
- `docs/OFFLINE_ACCEPTANCE_TESTS.md`
- `docs/LOCAL_SERVER_OPERATIONS.md`
- `.ai/OFFLINE_LICENSE_MODEL.md`
- `.ai/OFFLINE_SYNC.md`
- `.ai/CLOUD_OPTIONALITY.md`

## Important safety boundary
Software can provide auditability, validation controls and technical support for accreditation/regulatory workflows, but it must not claim certification merely because the software is installed. Clinical decisions remain with authorized personnel.
