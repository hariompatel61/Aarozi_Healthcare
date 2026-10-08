# Schema Map

Core groups:
- platform: tenants, branches, departments, licenses, devices
- identity: users, roles, permissions, role_permissions, user_roles, sessions
- patient: patients, patient_identifiers, documents/consents later
- pathology: tests, reference_ranges, profiles, packages, orders, order_items, samples, sample_events, results, result_values
- billing: invoices, invoice_items, payments, refunds, tax rules
- referral: referral_partners, referral_rules, commission_ledger, settlements
- reporting: report_templates, report_versions, reports, report_delivery
- blood_bank: donors, screenings, donations, blood_units, blood_unit_tests, cross_matches, blood_movements, adverse_events
- integration: analyzers, analyzer_mappings, analyzer_messages, webhook_events
- offline: devices, sync_events, sync_conflicts, local_backups
- observability: audit_logs, background_jobs

Canonical tenant rule: every tenant-owned row carries tenant_id unless it is provably global.
