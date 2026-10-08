# Aarozi Healthcare - Commercial Offline-First Model

## 1. Product promise
Aarozi Healthcare can be sold as a yearly offline/local license. The customer can run the core laboratory, pathology, billing, reporting and blood-bank workflows on a local LAN without Internet.

## 2. Example deployment

```text
                    LAB LAN
                      |
               AAROZI LOCAL SERVER
               PostgreSQL + API
                      |
        +-------------+-------------+
        |             |             |
      PC-01         PC-02         PC-03
                                     |
                                   PC-04

Optional later:
Local Sync Agent <----Internet----> Aarozi Cloud
```

For a 4-PC reception desk, all users see the same local patient/order/billing/report data. The computer does not define the role; RBAC defines permissions.

## 3. Offline operations
The following must continue with Internet disconnected:
- patient registration/search
- order entry
- billing/discount/payment/receipt
- sample collection/receiving
- barcode/QR generation
- result entry/verification/approval
- report preview/PDF/printing
- blood-bank donor/stock/testing/cross-match/issue workflows
- local inventory
- analyzer connector workflows supported by the local connector
- audit logging
- import/export
- local backup/restore

## 4. Offline licensing
The product is licensed by a signed annual license. The local server verifies the signed license using a public verification key. License issuance/renewal is an admin-side process and does not require the client installation to contact Aarozi.

### Never-online activation
1. Customer installation generates an activation request file.
2. Customer transfers the request using any permitted channel (USB/email/other machine).
3. Aarozi licensing console generates a signed license file.
4. Customer imports the license file into the local admin console.
5. Local server validates it without Internet.

## 5. Renewal
Before expiry, show configurable notices such as 30/15/7/1 day reminders. On expiry, do not erase or corrupt data. Enter the configured restricted state and allow a signed renewal file to restore active status.

## 6. Optional cloud plan
Cloud Sync is an optional subscription. It can be enabled later without reinstalling the local application. It can provide cloud backup, remote report access, remote administration, multi-branch aggregation and other subscribed features.

## 7. Sync design
Sync is local-first, batch-based, resumable and idempotent. Clinical and financial conflicts must never be resolved by blind last-write-wins.

## 8. Backup
Offline customers must have a local encrypted backup workflow. Cloud customers can add cloud backup. Backup is not complete until restore testing succeeds.
