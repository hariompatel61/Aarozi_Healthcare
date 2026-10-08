# Aarozi Healthcare - Offline Acceptance Test Plan

## A. Hard offline test
Disconnect Internet completely.

Verify:
- login works
- patient registration works
- patient search works
- order creation works
- billing works
- discount works
- payment receipt works
- barcode/QR works
- sample workflow works
- result entry/verification works
- report rendering/printing works
- blood-bank workflows work
- local audit works
- backup works
- import/export works

## B. Multi-PC test
With at least 4 clients on LAN:
- create patient on PC-1 and find on PC-2
- create bill on PC-2 and view on PC-3
- create sample on PC-3 and receive on PC-4
- release report on one station and print on another
- verify concurrent writes do not duplicate identifiers

## C. 5,000 patient day test
Generate realistic synthetic workload for at least 5,000 patients in one local day.
Measure:
- registration throughput
- patient search p95
- order creation p95
- billing p95
- result save p95
- report queue throughput
- database CPU/RAM/IO
- storage growth
- sync queue growth (if enabled)

Acceptance is based on measured thresholds defined in `.ai/PERFORMANCE_BUDGET.md` and hardware-specific capacity evidence, not on an assumption that 5,000/day is always comfortable.

## D. Offline-to-cloud test
1. Start fully offline.
2. Create representative changes.
3. Reconnect Internet.
4. Run initial sync.
5. Interrupt network during a batch.
6. Resume.
7. Verify no duplicate clinical/financial records.
8. Verify checkpoint recovery.
9. Verify large report files resume independently.

## E. Renewal test
- import valid license
- verify entitlements
- set near-expiry test fixture
- enter grace period
- verify restricted state
- export renewal request
- import renewed license
- verify full access restored
- verify no data loss

## F. Clock rollback test
Simulate a controlled system-clock rollback in a test environment. Verify the event is detected, audited and does not extend validity.
