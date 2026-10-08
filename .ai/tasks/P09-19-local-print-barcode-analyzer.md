# P09-19 - Offline Printing, Barcode/QR and Analyzer Continuity

## Objective
Ensure core device workflows continue without Internet.

## Dependencies
P09-18.

## Context files
- `docs/OFFLINE_DESKTOP.md`
- `docs/ANALYZER_INTEGRATION.md`
- `.ai/OFFLINE_LICENSE_MODEL.md`

## Implementation prompt
Verify and harden local printing, barcode/QR generation and supported analyzer connector flows so they do not depend on cloud services. Queue local output safely when a printer or analyzer is temporarily unavailable.

## Test / verification
Internet disconnected: print a final report, scan a barcode, generate a QR, send/receive analyzer test data using a supported local adapter, then restore the device.

## Done criteria
Core device workflows function fully on the local site network.
