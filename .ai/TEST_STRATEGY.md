# Test Strategy

## Unit
- permission resolution
- pricing/discount/commission calculations
- reference ranges and flagging
- state transitions
- template rendering primitives

## API
- authentication
- RBAC negative tests
- tenant isolation
- validation
- idempotency
- pagination

## Integration
- analyzer protocol parsing
- report PDF generation
- notifications
- payment callbacks
- storage adapters
- sync replay/conflict handling

## E2E
- registration -> order -> billing -> sample -> result -> approval -> report
- referral discount/commission
- donor -> component -> testing -> release -> issue
- offline -> reconnect -> sync

## Performance
- search latency
- queue list latency
- report render throughput
- concurrent writes
- sync throughput

## Recovery
- database restore
- offline backup restore
- failed worker retry
