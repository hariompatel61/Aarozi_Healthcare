# Aarozi Healthcare - Local Server Operations

## Target deployment
Use one dedicated local server on the site LAN for multi-PC deployments. Avoid independent databases on each workstation.

Recommended starting hardware for a small/medium diagnostic centre:
- modern 8-core CPU
- 16-32 GB RAM
- NVMe SSD
- 1 Gbps LAN
- separate backup destination
- UPS recommended

Actual hardware must be validated with workload testing.

## Services
- Aarozi local API/server
- PostgreSQL
- background worker
- report/PDF worker
- sync agent when cloud plan is enabled
- analyzer connector service

## Local operations
- health endpoint
- service status screen
- local database backup
- restore wizard
- license status
- storage usage
- printer test
- barcode/QR test
- analyzer connectivity test
- local network test

## Failure behavior
- internet failure: core operations continue
- cloud sync failure: local operations continue; queued changes remain durable
- report worker failure: reports remain queued and visible as pending
- printer failure: record remains printable later; do not silently lose report state
- local server failure: clients fail clearly and safely; restore/recovery procedure must be documented
