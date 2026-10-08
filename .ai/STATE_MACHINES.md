# State Machines

## Sample
ORDERED -> COLLECTED -> BARCODED -> RECEIVED -> ACCEPTED -> IN_PROCESS -> RESULT_READY
RECEIVED -> REJECTED (reason required)

## Result
DRAFT -> ENTERED -> VERIFIED -> RELEASED
RELEASED -> AMENDED (reason + new version + audit)

## Blood unit
COLLECTED -> TESTING -> QUARANTINED -> RELEASED -> RESERVED -> ISSUED
RELEASED -> EXPIRED / DISCARDED
ISSUED -> RETURNED only when policy allows

## Invoice
DRAFT -> ISSUED -> PART_PAID -> PAID
ISSUED -> CANCELLED only with authorized reason
PAID -> REFUND_PENDING -> REFUNDED where permitted

## License
PENDING_ACTIVATION -> ACTIVE -> EXPIRING -> GRACE -> EXPIRED_RESTRICTED
ACTIVE -> REVOKED
EXPIRED_RESTRICTED -> ACTIVE only after valid renewal/import
CLOCK_ROLLBACK -> RECOVERY_REVIEW
Do not delete operational data on expiry.

## Sync event
QUEUED -> BATCHED -> SENT -> ACKED
SENT -> RETRY_WAIT -> SENT
SENT -> FAILED (manual/automatic retry policy)

## Sync checkpoint
ACTIVE -> ADVANCED
ACTIVE -> STALLED -> ACTIVE
Checkpoint may advance only after server-side durable acknowledgement.
