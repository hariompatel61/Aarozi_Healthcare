# Agent Implementation Protocol

## Purpose
This file prevents context bloat, architecture drift and unsafe broad changes.

## Execution protocol
For each task:
1. Read the task file.
2. Read only its `Context files` list.
3. Inspect the existing implementation around the target area.
4. Write a 3-7 line implementation plan.
5. Implement the smallest complete change.
6. Add/update tests required by the task.
7. Run the task test commands.
8. Fix failures caused by the task.
9. Update the task status file or changelog if requested.
10. Stop.

## Context budget
Default context budget for an ordinary task:
- task file: 1 file
- global rules: 1 file
- maximum architecture/domain docs: 3 files
- maximum source code files to inspect before coding: 8 files unless the task explicitly needs more

Never paste the entire repository into the prompt.

## Change discipline
- No speculative refactor.
- No new dependency unless required by the task.
- No package swap without an ADR.
- No schema change without migration + rollback consideration.
- No permission change without negative authorization tests.
- No clinical result workflow change without audit/version tests.

## Test discipline
Every task must leave the repository in a testable state. A failing unrelated pre-existing test can be reported as pre-existing, but do not hide it.

## Completion format
When the task is complete, return:
- changed files
- tests run
- result
- any known follow-up
No long narrative.
