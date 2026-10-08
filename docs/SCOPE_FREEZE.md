# Aarozi Healthcare — Scope Freeze

**Status:** FROZEN  
**Freeze date:** 2026-10-08  
**Document version:** 1.0.0

---

## Product Identity

- **Product:** Unified Diagnostic Laboratory + Blood Bank + Billing SaaS
- **Commercial model:** OFFLINE_LOCAL annual license (primary), HYBRID_SYNC cloud plan (optional)
- **Architecture:** Modular monolith (ADR-001)

---

## MVP Scope (Phase 0–6)

### Modules included

| Module | Key entities | Notes |
|---|---|---|
| **Identity & RBAC** | tenant, branch, department, user, role, permission | Granular module/resource/action (ADR-004) |
| **Patient Management** | patient | Single shared identity across all workflows (ADR-002) |
| **Registration & Orders** | order, order_item, sample | Sample lifecycle management |
| **Pathology / LIMS** | test, profile, package, result, report, report_version | Result entry, verification, pathologist approval, amendment versioning |
| **Billing & Referral** | invoice, payment, referral_partner, referral_rule, commission_ledger | Price lists, discount engine, refunds |
| **Report Engine** | report_template | Versioned configuration, not hard-coded (ADR-005) |

### Deployment modes in MVP

| Mode | Description |
|---|---|
| **Cloud** | Multi-tenant SaaS, internet required |
| **Local multi-PC** | Local server as LAN source of truth (ADR-003), internet not required for core workflows |

### Cross-cutting MVP requirements

- Multi-tenant isolation at all layers
- Server-side authorization on every API route
- Audit trail for clinical and financial state changes
- No unbounded queries; server-side pagination everywhere
- Ultra-fast operational UI (keyboard-driven reception workflows)
- No hidden dependency on internet for core offline flows

---

## V1 Scope (Phase 7–9)

Adds on top of MVP:

| Module | Key entities | Notes |
|---|---|---|
| **Blood Bank** | donor, donation, blood_unit, cross_match | Full donation-to-issue lifecycle including TTI, quarantine, inventory, reservations, adverse events |
| **Analyzer Integration** | analyzer, analyzer_message | ASTM + HL7 adapters, machine mapping, sample matching |
| **Hybrid / Offline** | installation, license, activation_request, renewal_request, device, sync_event, sync_checkpoint, backup | Signed offline licensing, file-based activation/renewal, resumable sync, backup/restore |

### Additional V1 deployment modes

| Mode | Description |
|---|---|
| **Offline** | Fully disconnected site; file-based license activation |
| **Hybrid** | Local-first with optional cloud sync |

---

## V2 Scope (Phase 10–13)

Adds on top of V1:

| Area | Description |
|---|---|
| **UX Polish** | Unified shell, reception workspace, operational tables, keyboard workflow, lazy loading, cache strategy, UX performance gate |
| **Desktop & Mobile** | Tauri shell, local server installer, desktop printing, mobile auth, mobile sample collection, mobile blood bank |
| **Hardening** | Security hardening, API load tests, DB performance, frontend performance, report throughput, observability, backup recovery drill, regression suite |
| **Launch** | Demo tenant, pilot checklist, UAT, data migration, production hardening, pilot rollout, production release |

---

## Assumptions

1. **Single patient identity** — pathology, billing, reports and blood bank share one patient record per tenant (ADR-002).
2. **Local server for multi-PC** — four reception PCs need one local source of truth when internet is unavailable (ADR-003).
3. **Granular RBAC** — permissions are module/resource/action triples (ADR-004). No flat "admin vs user" dichotomy.
4. **Report templates are data** — versioned configuration, not hard-coded pages (ADR-005).
5. **Offline-first** — core clinical and financial workflows (registration, billing, sample, result, report, blood bank) must never require cloud connectivity.
6. **Licensing** — signed offline licenses verified locally; private signing keys never shipped in the client; clock rollback must not silently extend validity.
7. **No microservices in MVP** — modular monolith first (ADR-001); microservice extraction is a post-V2 concern.
8. **Clinical/financial data is durable** — license expiry must never delete or corrupt clinical/financial data.
9. **Audit records are append-only history** — clinical results and financial ledger entries are versioned; edits produce new versions.
10. **Sync is resumable and idempotent** — hybrid sync must handle interrupted connections gracefully.

---

## Open Decisions

| # | Decision | Status | Target Phase |
|---|---|---|---|
| OD-001 | Exact cloud hosting provider for SaaS tier | OPEN | V2 |
| OD-002 | WhatsApp/SMS notification provider selection | OPEN | V1 |
| OD-003 | NABL/ISO compliance report format requirements | OPEN | V2 |
| OD-004 | Third-party payment gateway integration specifics | OPEN | V1 |
| OD-005 | Mobile app distribution channel (Play Store vs enterprise sideload) | OPEN | V2 |
| OD-006 | Data residency requirements for cloud tenants | OPEN | V2 |
| OD-007 | Exact LIS instrument list for ASTM/HL7 adapter certification | OPEN | V1 |

---

## Boundary Rules

- **No feature creep into MVP** — blood bank, analyzer integration, and hybrid sync are V1.
- **No premature optimization** — measure before optimizing; keep performance budgets as targets not blockers during early phases.
- **No cloud dependency for offline** — every offline-approved flow must work with zero internet.
- **No uncontrolled schema changes** — every schema change requires migration + rollback consideration.
- **No new dependency without task justification** — package additions require explicit task linkage.
