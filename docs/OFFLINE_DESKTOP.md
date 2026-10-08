# Offline / Desktop

## Architecture
For a multi-PC site use a local server on the LAN. Desktop clients connect to the local API/server. The local PostgreSQL database is the site's source of truth.

## Core offline functions
- patient registration/search
- order creation
- billing/payment/discount
- sample handling
- result entry/verification/approval
- report rendering/PDF/printing
- barcode/QR
- blood-bank operations
- supported analyzer connectors
- audit logs
- import/export
- local backups

## License
A signed annual offline license is verified locally. No recurring license-validation call is required. Expiry moves the installation into a configured grace/restricted state without deleting data.

## Cloud upgrade
A customer may later import a license that adds cloud-sync entitlement. The same local installation is retained; cloud synchronization begins from a durable initial-sync checkpoint.

## Local failure model
- internet outage: application continues
- sync outage: local application continues and queues changes
- printer outage: report remains available for retry/reprint
- analyzer outage: local exception queue records the failure
- local server failure: use documented restore/recovery procedure
