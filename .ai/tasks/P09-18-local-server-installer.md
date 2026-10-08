# P09-18 - Local Server Installer and LAN Bootstrap

## Objective
Make local deployment reproducible for a lab with multiple desktop clients.

## Dependencies
P09-17.

## Context files
- `docs/LOCAL_SERVER_OPERATIONS.md`
- `docs/OFFLINE_DESKTOP.md`
- `docs/DEPLOYMENT.md`

## Implementation prompt
Create a deterministic Windows local-server installation flow with PostgreSQL, API, worker, health checks, local backup directories and first-run organization setup. Desktop clients must connect to the configured local server over LAN without requiring cloud DNS.

## Test / verification
Install on a clean Windows test VM, configure the LAN address, connect four clients, restart the server, and verify data persistence.

## Done criteria
A fresh local site can be installed repeatably without Internet dependency after installers are prepared.
