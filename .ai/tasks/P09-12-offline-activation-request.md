# P09-12 - Offline Activation Request

## Objective
Allow a never-online local installation to export an activation request and import a signed license file.

## Dependencies
P09-11.

## Context files
- `.ai/OFFLINE_LICENSE_MODEL.md`
- `docs/RENEWAL_AND_ACTIVATION.md`
- `contracts/offline-license.schema.json`
- `database/012_commercial_offline_license.sql`

## Implementation prompt
Implement only the offline file-based activation workflow. Generate an activation request with installation identity, module requests, limits, protocol version and nonce. Never include patient records. Provide import validation for the returned signed license. Make re-import idempotent.

## Test / verification
Test export/import with Internet disabled, malformed requests, duplicate nonce, wrong installation, invalid signature and idempotent re-import.

## Done criteria
A never-online customer can activate using file transfer only.
