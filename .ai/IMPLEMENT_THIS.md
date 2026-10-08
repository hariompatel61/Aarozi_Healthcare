# IMPLEMENT THIS

Paste this instruction into your IDE agent when selecting a task file:

> Implement the task described by the file path I provide. Read `.ai/AGENT_IMPLEMENTATION_PROTOCOL.md` first, then read only the task's `Context files`. Make the smallest complete change, add/update tests, run the task tests, and stop after the task acceptance criteria are green. Do not redesign unrelated parts. If the task is an offline/licensing task, do not add cloud dependency to core workflows and never ship production private signing keys.

Then provide exactly one task path, for example:

`.ai/tasks/P00-01-scope-freeze.md`

Offline commercial hardening starts at:

`.ai/tasks/P09-11-offline-license-signing.md`
