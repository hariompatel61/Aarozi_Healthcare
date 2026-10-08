# Context Router

Use this file to determine the minimum context for an AI coding task.

| Task area | Minimum context |
|---|---|
| Auth/RBAC | domain glossary + permissions + security rules |
| Tenant/branch | schema map + security rules |
| Patient | domain glossary + patient schema + API rules |
| Pathology | domain glossary + state machines + pathology doc |
| Billing | billing/referral doc + schema map + API rules |
| Reports | report engine doc + domain glossary + performance budget |
| Blood bank | blood bank doc + state machines + security rules |
| Analyzer | analyzer doc + event catalog + security rules |
| Offline | offline sync doc + state machines + schema map |
| UI/UX | UI system + performance budget + route/module map |
| Performance | performance budget + architecture + observability |
| QA | test strategy + task file + affected domain |

## Context compression rules
- Prefer machine-readable YAML/JSON for stable facts.
- Prefer summaries instead of repeating requirements.
- Reference files by path.
- Do not duplicate schema definitions in prompts; link the canonical schema file.
- Do not send old versions of a design after the canonical file has been updated.
