# P09-14 - Optional Cloud Entitlement

## Objective
Allow the same offline installation to add cloud sync later without reinstalling.

## Dependencies
P09-13.

## Context files
- `.ai/CLOUD_OPTIONALITY.md`
- `.ai/OFFLINE_LICENSE_MODEL.md`
- `.ai/OFFLINE_SYNC.md`
- `docs/COMMERCIAL_OFFLINE_MODEL.md`

## Implementation prompt
Implement feature entitlements centrally. Offline mode must not require cloud calls. Add a supported transition from OFFLINE_LOCAL to HYBRID_SYNC by importing an upgraded license/entitlement. Cloud feature gating must be centralized and testable.

## Test / verification
Start without cloud entitlement, upgrade via signed license, verify sync features appear without reinstall, and verify local workflows remain functional if cloud is unavailable.

## Done criteria
Cloud is optional and upgradeable in place.
