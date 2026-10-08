# AI Token Optimisation

## Goal
Build the system with high AI productivity while keeping prompt/context size low.

## Rules
1. One task file = one AI turn whenever possible.
2. Use file paths, not pasted documents.
3. Keep domain truth in canonical machine-readable files.
4. Never ask an agent to regenerate the architecture from memory.
5. Use `git diff` + tests as the feedback loop.
6. For a bug, provide the smallest failing test and the relevant file, not the entire module.
7. Use compact acceptance criteria.
8. Keep generated code local to the requested module.
9. Summarize completed decisions into `.ai/decisions/` instead of repeating them in every prompt.
10. Use the task dependency graph so agents do not inspect future modules too early.

## Token-saving command pattern

"Implement `.ai/tasks/P05-03-result-value-model.md`. Read the task's Context files only. Do not inspect unrelated domains. Run the listed tests."

## Preferred agent output
- 1 short plan
- implementation
- tests
- concise summary

## Avoid
- "Review entire codebase"
- "Optimize everything"
- "Build the whole module"
- repeating the 40-page BRD in every task

## Offline/licensing token rule
For offline licensing tasks, read only:
- `.ai/OFFLINE_LICENSE_MODEL.md`
- `docs/RENEWAL_AND_ACTIVATION.md` when activation/renewal is involved
- `docs/OFFLINE_ACCEPTANCE_TESTS.md` when validation/load testing is involved
- the task file itself

Do not load the full BRD/PRD unless the task explicitly points to a requirement that is not present in the canonical context files.
