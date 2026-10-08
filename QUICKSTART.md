# Quick Start - Aarozi Healthcare

1. Extract ZIP.
2. Open the extracted `Aarozi_Healthcare` folder in your IDE.
3. Read `COPY_THIS_PATH_FIRST.txt`.
4. Start development infrastructure if needed:
   `docker compose -f docker-compose.dev.yml up -d`
5. In the AI coding agent, provide ONE task path from `.ai/tasks/` and say:

   `Implement this task file. Read the task protocol and only the referenced context files. Make the smallest safe change, add/update tests, run the listed tests, and stop when green.`

6. Start with `.ai/tasks/P00-01-scope-freeze.md`.
7. After each phase exit gate passes, continue to the next phase.

## If building the offline commercial path
After the base modules are ready, continue through:
`P09-11` → `P09-20`.

## Key principle
Do not paste the entire project or the full 41-page requirements document into the agent prompt on every task. The task file is the context router.
