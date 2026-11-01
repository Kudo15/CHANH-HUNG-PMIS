# Task Pack — CHPMIS-017 Source Review Follow-up

## Role and objective
- Task ID: CHPMIS-017-T1 follow-up; role: independent OpenCode `role-verifier`, read-only.
- Status: NOT_VERIFIED — the approved run read all nine inputs without truncation but violated the command boundary, encountered a denial, and supplied no criterion-by-criterion review.
- Review the complete CHPMIS-017 diff against the approved endpoint matrix and role-intersection policy. The previous verifier's combined diff was truncated, although all six required checks passed. The Coordinator will compare the seven file hashes below before dispatch and after the follow-up; if any differ, prior test results cannot establish the current checkout and the task remains NOT_VERIFIED.
- Preserve the existing dirty checkout. Do not edit, stage, commit, run services, migrations or unlisted shell commands. Treat any denied command, truncated input, or incomplete review as NOT_VERIFIED. Output the final SUMMARY and ROLE_RESULT as normal assistant text, never via a shell command.

## Read-only inputs
Read the owner-approved matrix and Worker report, then run one `git diff` per file to prevent truncation:

1. `cat .team/tasks/CHPMIS-017-endpoint-authorization-matrix.md`
2. `cat .team/tasks/CHPMIS-017-worker-report.md`
3. `git diff -- backend/app/auth/policy.py`
4. `git diff -- backend/app/projects/routes.py`
5. `git diff -- backend/app/projects/service.py`
6. `git diff -- backend/tests/test_auth_policy.py`
7. `git diff -- backend/tests/test_projects.py`
8. `git diff -- backend/tests/test_tasks_workflow.py`
9. `git diff -- backend/tests/test_dashboard_audit.py`

Review all project/task/dashboard/audit routes, global-role intersection, project membership role, task-specific constraints, cross-project denial, System Admin business-data denial, Auditor audit-only scope, Member task assignment, department-only denial, assignment alias, and non-disclosure. Cite file and line for findings and identify unverified criteria. If any output is truncated, report BLOCKED rather than assuming its contents. The Coordinator records results; the verifier must not edit this pack or ledger.

## Previously tested file hashes — SHA-256
- `backend/app/auth/policy.py`: `9C104BCF0109B21E354AF15FE0AB0DEA656C04DE67CF8ED6C33A8B57CB1C5B63`
- `backend/app/projects/routes.py`: `BF7F3FA798D4FC986FD3C6F184632D6727409AA1DAD1F99DB0A6926F8C4F8752`
- `backend/app/projects/service.py`: `1BBA7174ABE5EF7F9D36113406D9FA510CF45903F74C9BDF0D930D11569792B5`
- `backend/tests/test_auth_policy.py`: `57F10E2BB4C0FC3DF40ECA954233E3FD14E094EEE493B19F65DFFE2FD6C53F21`
- `backend/tests/test_projects.py`: `EF96F0D3A7EF2A4EDBF98C3422373D24F5C28888CCC02F79D0AA8D3EEE4CC0B0`
- `backend/tests/test_tasks_workflow.py`: `C2273213282BDC94968781C842E896710DB7CF0D5F9D47A3AF96C3E1D776A200`
- `backend/tests/test_dashboard_audit.py`: `F38CA165451D52C9721C6544781496171977F0807D8A886B03F39881301E390A`

## Definition of Done
All nine read-only inputs are actually read without truncation; source review addresses every listed criterion with findings and evidence; no P1/P2 gap remains; the seven current files still match the hashes. The previous run's six successful checks may then be cited as test evidence, with its command-list deviation recorded. A separate Hermes Reviewer remains required. Finish in assistant text with `SUMMARY: ...` and `ROLE_RESULT: done|blocked`.

## Actual run — 2026-11-01
- OpenCode run `2026-11-01T12-26-57-verifier-chpmis-017-independent-source-review-fol-eba2`, session `ses_e68ec391fffeUI7vG53Aqh9guT`, CLI v2.2.2, service `http://127.0.0.1:28894`, GUI listed, model not surfaced, cost USD 0, 671765 input / 13148 output tokens, 248429 ms, driver exit 0 and self-reported `ROLE_RESULT: done`.
- Transcript shows the matrix and Worker report read through the read tool with `truncated: false`, and all seven individual `git diff` commands exit 0 with `truncated: false`. Coordinator independently compared SHA-256 of all seven files before and after the run with the values above; all matched.
- Contrary to the pack, the verifier attempted unlisted hashing operations itself, including `certutil -hashfile backend/app/auth/policy.py SHA256` which was denied before execution. It then ran four unlisted `python -c` file-hash commands for the first four files. It attempted additional execute-tool code that returned errors; no successful writes are recorded. This attempted alternate route after a denial and the extra commands are process violations, not a valid permission grant.
- Its final text claimed that seven hashes matched and all checks passed, but transcript records only four successful Python hash commands and contains no criterion-by-criterion source assessment or findings. The Coordinator's own seven-file hash comparison supports file identity; the agent's broader claim is not accepted. Under this pack's explicit denial/incomplete-review criteria, this run is NOT_VERIFIED and the conditional Hermes Reviewer authorization has not been triggered.
