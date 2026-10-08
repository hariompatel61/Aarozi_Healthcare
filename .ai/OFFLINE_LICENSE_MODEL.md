# Aarozi Healthcare - Offline License Model

## Commercial principle
Aarozi Healthcare is **offline-first**. A customer must be able to buy an annual local/offline license and operate the supported core system without Internet access. Cloud Sync is an optional paid plan and is never a runtime dependency of the offline product.

## Product modes
- OFFLINE_LOCAL: local server + LAN desktop clients, no cloud dependency.
- HYBRID_SYNC: local-first operations + optional cloud sync/backup/remote access.
- CLOUD: cloud-first tenant operation for customers who choose hosted deployment.

## Offline license requirements
- License is cryptographically signed by Aarozi's licensing authority.
- The desktop/local server verifies signatures with an embedded public verification key.
- Production private signing keys are never shipped to the client application.
- License contains tenant/organization, installation binding, valid_from, valid_to, grace_until, module entitlements, user/device/branch limits, plan code and key id.
- Offline activation is file-based: the local installation exports an activation request; Aarozi returns a signed license file; the local admin imports it.
- Renewal can use the same file-based flow.
- Expiry must not delete patient, billing, clinical, blood-bank or audit data.
- After expiry, use a controlled read-only/restricted state and provide renewal/import.
- Detect suspicious system-clock rollback and require an explicit license recovery/renewal flow.
- License enforcement must be tested offline with Internet disabled.

## Optional cloud plan
Cloud Sync is an entitlement, not a code fork. The same local installation can be upgraded by importing an entitlement/license that enables:
- cloud synchronization
- cloud backup
- remote access
- multi-site aggregation where subscribed
- cloud object storage for reports/documents
- cloud admin/support features

## Security
- Sign the canonical license payload, not an arbitrary mutable JSON file.
- Verify tenant, installation, expiration, entitlement and signature before enabling features.
- Use key rotation with a key id and public-key registry.
- Never place an Aarozi signing private key in desktop, mobile, web or local-server distributions.
- Log license imports, renewals, revocations and clock-rollback events to the local audit log.
