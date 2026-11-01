# CHPMIS-013-R1 — Independent Reviewer Contract

## Task and role

- **Task ID:** CHPMIS-013-R1
- **Role:** Separate Hermes Reviewer; read-only, independent from the Worker.
- **Parent:** CHPMIS-013; audit A1-01–A1-04; mission §4 A1; platform AC-01/03/04.
- **Workspace:** Current repository at `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`; preserve all dirty files and do not commit.

## Review scope

Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, CHPMIS-013 task pack, Worker report, Coordinator runtime evidence, relevant audit register, and the CHPMIS-013-only diff for:

- `.github/workflows/ci.yml`
- `backend/alembic/versions/0005_initial_admin_bootstrap.py`
- `backend/tests/test_postgresql.py`
- `backend/tests/test_projects.py`
- `.team/tasks/CHPMIS-013-worker-report.md`

Keep prior CHPMIS-014 changes separate. Verify the allowlist, exact revision/table set, CI placeholders limited to the config-validation step, and that migration changes are formatting-only. Compare the Worker claims with exact test and runtime evidence. Check the empty-database upgrade, populated 0004-to-head upgrade, preserved synthetic rows, and observed downgrade failure against the Coordinator evidence. State clearly that A1-04 remains an unsafe confirmed rollback limitation and remote CI is NOT_VERIFIED.

## Boundaries

- Do not edit files, run formatters, execute tests, inspect secrets, read `.env`, use Docker, modify databases, commit, push, merge, deploy, or access production/remote systems.
- Do not claim the downgrade is safe or that the broader mission/platform gate is complete.
- Report each finding with severity P1/P2/P3, `file:line`, impact, and correction direction. End with `APPROVED` or `CHANGES_REQUESTED`; if evidence is insufficient, state exactly what remains NOT_VERIFIED and request changes rather than guessing.

## Review DoD

- Independent source/diff review complete and tied to the current working diff.
- Scope, schema contract, CI interpolation, migration history, runtime evidence, and known rollback boundary evaluated.
- No reviewer edits or unassigned tests/runtime actions.
- Finish by calling exactly one Hermes card closeout action: `kanban_complete(result=...)`, `kanban_request_changes(reason=...)`, or `kanban_block(reason=...)`.
