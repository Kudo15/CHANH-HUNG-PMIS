# Task Pack — CHPMIS-008-T1 Independent Tester

- **Task ID:** CHPMIS-008-T1.
- **Role:** Independent Tester / Verifier, OpenCode `role-verifier`.
- **Scope:** Read `CHPMIS-008` task pack; run only the focused test and full backend pytest suite listed there; make no edits.
- **Prompt template:** Test Engineer Agent Role, prompts.chat ID `cmmx34zl7000vil04rm2wl8yl`, retrieved/adapted in `.team/tasks/CHPMIS-008-ac10-department-scope-integration.md`.
- **Model:** inherit active OpenCode configured default; omit `--model`.
- **Workspace:** repository root; run sequentially after Worker.
- **DoD:** report exact command, working directory, output, exit code, AC-10 assertion coverage, and `NOT_VERIFIED` evidence; no fixes.
- **Trace:** AC-10, HG2 explicit-membership rule, CHPMIS-008 test function.

## Commands (from `backend/`)
- `.venv\Scripts\python.exe -m pytest -q tests/test_projects.py::test_department_match_without_explicit_project_membership_is_denied_ac10`
- `.venv\Scripts\python.exe -m pytest -q`

End with `SUMMARY: ...` and `ROLE_RESULT: done|review|blocked` per the installed OpenCode verifier contract.

## Actual run
- **Retry authorization (2026-10-31):** The user explicitly authorized enabling OpenCode shell for this verifier and rerunning only the two pytest commands above. Keep `edit: deny`; make no source edits or run other commands.
- Initial run `2026-10-30T10-23-36-verifier-chpmis-008-t1-independent-backend-verifi-3505`; session `ses_e73a9e09dffeh1NaKxghstDr0T`; `gui_visible=true`; both commands were denied before execution with `permission.rejected: Permission denied: shell`; role result `blocked`.
- Authorized retry `2026-10-30T23-02-55-verifier-chpmis-008-t1-independent-backend-verifi-f8f9`; session `ses_e70f2ada4ffeY96OSNGghKnAKQ`; `gui_visible=true`; OpenCode CLI v2.2.2; configured default model was not exposed (`model_used=null`); cost recorded 0; tokens 12068/1624/597.
- Focused command from `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_projects.py::test_department_match_without_explicit_project_membership_is_denied_ac10` — `1 passed, 1 warning in 2.87s`, exit 0.
- Full suite from `backend/`: `.venv\Scripts\python.exe -m pytest -q` — `62 passed, 1 skipped, 1 warning in 6.22s`, exit 0. Warning: Starlette/httpx TestClient deprecation. `ROLE_RESULT: done`.
- Static assertion coverage mapped at `backend/tests/test_projects.py:430-541`; focused test execution independently verified it. Ruff was not run by T1 because it is outside the two-command scope.
