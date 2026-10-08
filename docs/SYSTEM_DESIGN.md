# Aarozi Healthcare - System Design

## High-level
Browser / Tauri / Flutter clients -> API -> domain modules -> PostgreSQL + Redis + object storage.

## Domain modules
Platform, Identity/RBAC, Patient, Pathology, Billing, Referral, Reporting, Blood Bank, Inventory, Integrations, Sync, Licensing, Notifications.

## Deployment modes
Cloud SaaS, local multi-PC, offline/hybrid.

## Service extraction
Do not split into microservices initially. Preserve internal module boundaries and event contracts.

## Request path
UI -> auth/session -> authorization -> application service -> transaction -> event/outbox -> background worker.
