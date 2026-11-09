# Phase 2 Remediation and Labs Subdomain Architecture

**Repository:** `hariompatel61/Aarozi_Healthcare`  
**Baseline:** `610c62347bdfbd00a26cebed9fd4830a0877250f`  
**Working branch:** `phase-2-remediation-labs-domain`

## Non-negotiable scope boundary

- The existing `https://aarozi.in` website and all of its current services must continue to operate exactly as they do today.
- Do not edit, replace, redirect, migrate, rebrand, or change DNS, hosting, SSL, CDN, analytics, forms, APIs, or deployment configuration for `aarozi.in`.
- Do not change the apex/root domain, its `www` host, or any existing root-domain routes.
- All new Aarozi Healthcare LIS marketing, product, lead-generation, download, documentation, and customer-portal web experiences belong exclusively under **`https://labs.aarozi.in`** and its explicitly approved subdomains.
- Treat the LIS website deployment as an independent application and release pipeline. A failure or deployment rollback on `labs.aarozi.in` must not affect `aarozi.in`.

## 1. Domain and hosting architecture

Use an independently managed DNS record for `labs.aarozi.in` pointing to the new LIS website hosting target. Do not alter existing apex or www records. Configure TLS/SSL for `labs.aarozi.in` only.

Recommended separation:

| Host | Responsibility | Change policy |
|---|---|---|
| `aarozi.in` | Existing business website/services | **Untouched; no changes** |
| `www.aarozi.in` | Existing www experience, if configured | **Untouched; no changes** |
| `labs.aarozi.in` | Aarozi Healthcare LIS public website | New independent deployment |
| `api-labs.aarozi.in` | Optional public-facing LIS licensing/commerce API, only if required | Separate service, explicit security review |
| Customer lab Master PC | Local LIS API/database | Customer-controlled; not hosted on public marketing site |

Do not expose a laboratory's local API or patient database directly to the public internet. The marketing website must not proxy, collect, or store patient-identifiable clinical data.

Before DNS or hosting changes, document the current DNS provider, hosting target, deployment owner, rollback procedure, and certificate process. Only create the new subdomain record after the destination is approved. No DNS write is authorized by this document.

## 2. Product positioning and brand system

Create a dedicated product identity for **Aarozi Healthcare** under the existing Aarozi brand family.

Brand direction:
- Product name: **Aarozi Healthcare**
- Descriptor: **Laboratory Information System (LIS)**
- Primary positioning: reliable, offline-first laboratory operations for diagnostic laboratories.
- Supporting themes: patient data control, accurate reporting, secure local operation, LAN workstations, backup and recovery, and practical laboratory workflows.
- Tone: professional, trustworthy, clinical, clear, and evidence-led. Avoid unsupported claims such as "100% secure", "zero downtime", "fully compliant", or "production proven".
- Preserve existing Aarozi brand assets only when their ownership and usage rights are confirmed. Do not copy or alter the existing `aarozi.in` site theme or assets without approval.
- Create a distinct visual system for the LIS product: accessible typography, high-contrast clinical UI, restrained healthcare palette, clear product screenshots, and consistent iconography.

All feature claims, plan limits, analyzer compatibility, certifications, security claims, and customer testimonials must be traceable to verified product evidence. Mark unimplemented features as planned, not available.

## 3. Website information architecture for labs.aarozi.in

Create a responsive public-facing website with these initial pages:

1. **Home** — product value proposition, intended lab segment, core capabilities, clear demo/contact CTA.
2. **Product** — LIS overview and verified modules.
3. **Features** — patient registration, sample collection, pathology/biochemistry, hematology, billing, reports, barcode printing, analyzer integrations, user roles, audit trail, offline/LAN mode. Publish only features verified in code and acceptance testing.
4. **Offline & LAN architecture** — explain Master PC and LAN workstation model, supported deployment topology, limitations, and backup responsibilities.
5. **Security & data ownership** — explain local data storage, access controls, encryption where implemented, backup destinations, retention, and support access. Never promise controls that have not been implemented.
6. **Backup & recovery** — describe verified local/USB/NAS/customer-owned cloud backup and tested restore workflow.
7. **Pricing** — display only approved plans, taxes, entitlements, renewal rules, branch policy, and workstation policy sourced from the actual commercial configuration.
8. **Demo / Contact sales** — validated lead form with consent, spam protection, and privacy notice.
9. **Downloads** — publish signed installer and release notes only after Windows clean-install, malware scanning, checksum, and upgrade/rollback acceptance checks.
10. **Documentation / Support** — versioned user guides, troubleshooting, support channels, and known limitations.
11. **Privacy policy, Terms, Refund/Cancellation, and Contact** — reviewed and approved before public launch.

Potential future authenticated areas (not part of the public marketing MVP):
- `labs.aarozi.in/portal` — customer account, license status, invoices and support requests.
- `labs.aarozi.in/downloads` — authenticated or public release distribution as decided by release policy.

Do not expose admin endpoints, internal API docs, test routes, environment diagnostics, or customer records through the public website.

## 4. Website technical and deployment requirements

- Keep the marketing website deployment independent from the Windows LIS application and customer Master PC.
- Use a separate build/deploy workflow, environment variables, secrets, logs, and rollback process for `labs.aarozi.in`.
- Do not make the existing `aarozi.in` deployment a dependency of the LIS site.
- Enforce HTTPS, secure response headers, CSP appropriate to the chosen framework, rate limiting on forms/authentication, server-side validation, and bot/spam controls.
- No secrets, OAuth refresh tokens, payment secrets, private signing keys, patient data, or database files in frontend bundles or public assets.
- If payments are enabled, use a trusted gateway with server-side signature verification and persistent order/webhook records. Do not trust client-supplied price, plan entitlement, or payment-success state.
- Use privacy-minimizing analytics and consent controls where required. Do not send health or patient data to analytics.
- Add SEO metadata, canonical URLs scoped to `labs.aarozi.in`, sitemap, robots policy, Open Graph metadata, accessible semantic HTML, and performance budgets.
- Configure monitoring and error reporting without capturing patient data or secrets.
- Include a staging environment on a separate approved hostname before production deployment.
- DNS, hosting, payment gateway, email provider, and production secret configuration require explicit owner approval and must not be guessed.

## 5. Phase 2 application remediation workstreams

### P0 — Database architecture
1. Make production SQLite selection explicit for the Windows Master PC.
2. Remove production reliance on the development-only `dev_aarozi.db` path.
3. Store the database in a configurable data directory outside the application installation directory.
4. Configure and test WAL, foreign keys, busy timeout, transaction boundaries, and concurrent LAN access.
5. Ensure migrations are versioned, transactional where possible, backed up, and recoverable.
6. Never place a live SQLite database file in Google Drive, Dropbox, or another file-sync folder.

### P0 — Google Drive security
1. Protect OAuth tokens at rest using Windows DPAPI or an equivalent OS-backed secret store.
2. Remove hardcoded fallback client credentials and test secrets.
3. Implement cryptographically random OAuth state, state validation, CSRF protection, and strict redirect URI allowlisting.
4. Implement refresh, revoke, disconnect, and reauthorization handling.
5. Scope token storage and backup metadata to the correct laboratory/tenant.
6. Ensure patient data is never sent to Aarozi central cloud infrastructure unless a separately approved architecture and explicit customer consent authorize it.
7. Log operational outcomes without logging tokens, authorization codes, or patient data.

### P0 — Backup and restore
1. Resolve the active database path through the database configuration/service, not a hardcoded development path.
2. Use SQLite Online Backup API for consistent snapshots.
3. Verify SHA-256 checksums and SQLite integrity before restore.
4. Create and verify a pre-restore safety snapshot.
5. Restore to a temporary location, validate it, then perform a controlled swap with rollback on failure.
6. Verify `PRAGMA integrity_check` and `PRAGMA foreign_key_check` after restore.
7. Support customer-selected local, removable USB, NAS, and customer-owned Google Drive destinations where implemented and tested.
8. Do not claim cloud backup works until OAuth, upload, retention, restore, and failure-recovery tests pass.

### P0 — Payment and licensing
1. Replace in-memory order and webhook state with durable database records.
2. Add unique constraints for gateway order/payment/event identifiers and durable idempotency.
3. Make payment confirmation, entitlement issuance, and audit events transactional or safely reconcilable.
4. Add a retry/reconciliation workflow for payment-success/license-issuance failures.
5. Model one physical laboratory/network license separately from workstation count; confirm the final commercial policy before enforcing it.
6. Treat each physical branch as a separately registered/licensed entity if that is the approved business policy.
7. Preserve access to patient records, reports, and data export after subscription expiry. Expiry must not destroy or hold patient data hostage.
8. Never issue a license solely from a frontend success redirect.

## 6. Branching, implementation and review rules

- Preserve the baseline commit and work only on `phase-2-remediation-labs-domain` (or reviewed child branches).
- Do not push directly to the default branch or merge without review.
- Inspect every target file and its callers/tests before editing.
- Make small, focused commits grouped by workstream.
- Do not delete functionality or weaken validation to make tests pass.
- Do not replace real integrations with mocks in production code.
- Add regression tests for every defect and update docs only after behavior is verified.
- Keep website work isolated from LIS API/database work where practical.
- Never change root-domain DNS, hosting, source code, redirects, content, analytics, or deployment.
- Record every assumption and unresolved decision instead of inventing credentials, policies, provider settings, or legal claims.

## 7. Required verification and acceptance evidence

For each workstream, report:
- changed file paths and commit SHA;
- test command and unedited test output/exit status;
- migration and rollback evidence;
- concurrency test results under realistic LAN load;
- backup/restore drill results, including integrity checks;
- OAuth security tests and token-storage platform coverage;
- payment webhook replay/idempotency and reconciliation tests;
- Windows 10/11 clean install, upgrade, uninstall, and recovery results;
- website staging URL, accessibility/performance/security checks, and deployment rollback result;
- explicit list of blocked/not-tested items.

A test passing in isolation is not proof of commercial production readiness. Do not claim launch readiness until the complete critical acceptance suite passes.

## 8. Launch gates

Do not publish the LIS website or installer as production-ready until:
1. Product claims match tested functionality.
2. Privacy/terms/refund policies have owner/legal review.
3. Public forms and any payment integration pass security testing.
4. Installer is signed, checksummed, and passes clean Windows installation and upgrade tests.
5. Backup and restore drills pass on supported customer configurations.
6. Critical security and data-integrity findings are closed.
7. `labs.aarozi.in` is verified over HTTPS and its rollback path is tested.
8. Existing `aarozi.in` has been confirmed unchanged.

**Final non-negotiable:** `aarozi.in` must continue operating exactly as it does today. All new LIS web architecture and branding must live on `labs.aarozi.in` only.
