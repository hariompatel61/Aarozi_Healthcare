# Aarozi Healthcare - Activation and Renewal Runbook

## Activation request
The local installation exports a signed/identified activation request containing only the minimum metadata needed to issue a license. Do not include patient records in the activation request.

Suggested fields:
- product version
- organization id/local tenant id
- installation id
- server fingerprint hash
- requested mode
- requested modules
- device/branch/user limits
- request nonce
- request timestamp
- request protocol version

## Signed license
A signed license contains:
- license_id
- tenant_id
- installation_id
- plan_code
- mode
- valid_from
- valid_to
- grace_until
- entitlements
- limits
- signing_key_id
- algorithm
- issued_at
- license_version
- signature

## Verification
The local server must verify:
1. schema/version
2. signature
3. signing key id
4. tenant binding
5. installation binding
6. time validity
7. entitlement consistency
8. license status

## Renewal
A renewal request can be produced on the offline installation. Aarozi returns a new signed license. Existing data stays untouched.

## Clock rollback
Store durable last-trusted-time metadata and the last accepted license state. If the observed local clock moves materially backwards, mark a clock rollback event, keep the application in a safe state and require explicit administrative recovery/renewal rather than silently extending the license.
