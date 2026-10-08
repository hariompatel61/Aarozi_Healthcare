# P09-11 - Offline License Signing

## Objective
Implement a signed offline license document and local signature verification using an asymmetric signing algorithm.

## Dependencies
P09-10, core license tables, tenant/installation identity.

## Context files
- `.ai/AGENT_IMPLEMENTATION_PROTOCOL.md`
- `.ai/OFFLINE_LICENSE_MODEL.md`
- `contracts/offline-license.schema.json`
- `database/012_commercial_offline_license.sql`
- `.ai/SECURITY_RULES.md`

## Implementation prompt
Implement P09-11 only. Add a canonical license payload serializer, Ed25519 signature verification, key-id handling, and license validation. Production private signing keys must never be shipped to clients. Add development-only test fixtures without committing production secrets. Keep the client verifier usable with no Internet.

## Test / verification
- valid signature accepted
- tampered payload rejected
- wrong tenant rejected
- wrong installation rejected
- expired license rejected
- unsupported algorithm rejected
- unknown signing key rejected
- no network call required

## Done criteria
Signed-license verification is deterministic, auditable and covered by unit tests.
