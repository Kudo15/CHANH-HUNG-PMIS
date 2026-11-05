# CHPMIS-020 — Windows Registry Reader Byte Safety and CI Coverage

## Task identity

- **Task ID:** CHPMIS-020
- **Roles:** Hermes Backend Worker → OpenCode read-only Tester + separate OpenCode Reviewer
- **Status:** IN_PROGRESS — Worker implementation and OpenCode Reviewer approval are recorded. OpenCode Tester passed frontend checks; retry T2 independently passed all 45 bootstrap tests, then its Ruff command was denied and it stopped. Coordinator's 2026-11-03 rerun passed the full backend suite with 7 PostgreSQL skips, Ruff and format; independent backend evidence remains partial. GitHub Actions run #3 exists for the exact baseline SHA and failed the backend job; the current local platform-separation/Windows-job changes have no candidate-SHA run. See `.team/tasks/CHPMIS-025-AC04-ci-run-diagnostic.md`. The prior CHPMIS-013-F1 and CHPMIS-017-F2 gateway incident history is recorded below; both cards were left to finish as owner directed.
- **Trace:** mission “CI xanh và demo nghiệp vụ thật” §3 A1/A2 and §6; CHPMIS-016 fixed-source trust-reader contract; `.github/workflows/ci.yml`.
- **Baseline:** branch `audit-remediation/verify-audit-findings`, HEAD `f13fb67d037c4f4c1552da82c04b5c0e60af5d5a`. Preserve all existing work, including untracked `.worktrees/`.

## Objective

Keep production Registry access fail-closed while correcting the signed-byte conversion defect in `WindowsRegistryBackend`, separating platform-guard coverage from Win32-internal coverage, and ensuring the Win32 mock tests execute in a Windows CI job.

## Current reproduction evidence

- On the Windows checkout, `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py::test_windows_registry_backend_null_pointers_and_cleanup_on_error` → `1 passed, 1 warning`, exit 0. Pytest warned that it could not write its cache under the protected backend temp/cache location.
- Exact current conversion reproduction from `backend/`: `.venv\Scripts\python.exe -c "import ctypes; b=(ctypes.c_byte * 3)(0x7f,0x80,0xff); print('signed_values=',list(b)); print(bytes(b[:3]))"` → values `[127, -128, -1]`, then `ValueError: bytes must be in range(0, 256)`, exit 1.
- Current workflow defines only `ubuntu-latest`; the CI test failure described in the mission is not reproduced on this Windows host because the production non-Windows guard precedes the mocked Win32 internals.
- GitHub connector returned no combined statuses or pull-request workflow runs for the baseline SHA. Local checkout has no configured Git remote. Remote CI remains `NOT_VERIFIED` until a run is available; do not add a remote or push.
- Hermes preflight initially failed inside the sandbox with `install state is not writable by this user` for lock files under `C:\Users\ANHVU\AppData\Local\hermes\installs`. Read-only ACL inspection showed that the install is owned by `ANHVU` and grants that account Full Control; no ACL, install file, board, or profile was changed. Outside-sandbox preflight succeeded. The gateway default lock path was unusable, so a temporary supported `HERMES_GATEWAY_LOCK_DIR` was used for the foreground session only; no persistent service or config was installed.
- A broad Hermes `dispatch --max 1` unexpectedly spawned `t_77f2dbd0`, title `CHPMIS-013-F1 Current Head PostgreSQL Schema Gate`, despite the read-only ready queue having shown only CHPMIS-020 `t_cda4f94d`. Owner directed it to finish; it became `done` at 2026-11-02 10:19 UTC, and no product edits appeared in checkout status. The gateway also started CHPMIS-017-F2 card `t_1ef0b522`; owner directed it to finish. Its latest run status is `running` but PID `168128` is absent. It is left untouched.
- CHPMIS-020 run 127 PID `24112` is also absent, while the card remained `running`. After confirming with both `Get-Process` and `tasklist`, the stale CHPMIS-020 card was reclaimed and exact-claimed (no queue dispatch). It is ready to launch directly as the authorized Worker. The last checkout status showed only Coordinator documentation changes and pre-existing untracked `.worktrees/`; no product code edits were observed.

## Scope and boundaries

Only these files may change:

- `backend/app/auth/bootstrap_admins.py`
- `backend/tests/test_admin_bootstrap.py`
- `.github/workflows/ci.yml`
- Append-only `.team/tasks/CHPMIS-020-worker-report.md`

No Registry provisioning/access, real keys, ACL or firewall changes, host account changes, production/provider access, schema/migration changes, secret reads, reset/clean/stash, stage/commit/push, merge, release, or deployment. Do not weaken the non-Windows production guard or change the trust source, path, view, ACL requirements, public-key validation, or cleanup contract.

## Required implementation

1. Keep an explicit non-Windows platform-guard regression that proves the production method rejects non-Windows before attempting Win32 calls.
2. Separate tests that exercise mocked Win32/ctypes internals from the non-Windows guard. Mark only truly Windows-specific tests with an appropriate platform skip; record the skip reason and the Windows CI job that runs them.
3. Fix conversion of `RegEnumValueW` binary data using an unsigned buffer or bounded raw-byte extraction. Respect `cb_data` and the existing 32-byte Ed25519 contract.
4. Add a regression through `WindowsRegistryBackend.read_trusted_keys()` with a valid synthetic 32-byte Ed25519 public key containing `0x80` and `0xff`; assert exact byte preservation. Do not substitute `SyntheticRegistryBackend` for this production reader path.
5. Retain or add negative assertions for invalid public-key type/length, Win32 API failure, and handle/security-descriptor cleanup on error. Keep all Win32 calls mocked; never provision or inspect Registry keys.
6. Add a Windows GitHub Actions job (Windows runner) that installs the backend test dependencies and executes the Win32 reader/ctypes/cleanup tests. Leave the existing Linux job responsible for full backend tests and its PostgreSQL service. Keep the platform guard tested on Linux.

## Acceptance criteria

- [x] RED/GREEN evidence shows the new production-reader regression fails on the signed-byte conversion and passes after the minimal correction.
- [x] The non-Windows fail-closed guard remains covered separately and production code behavior is unchanged.
- [x] Linux skips are limited to tests that invoke Windows-specific internals, have clear skip reasons, and are covered by the Windows CI job configuration.
- [ ] Windows CI runs the Win32 mock tests, including signed bytes and cleanup/error cases, without touching real Registry state.
- [x] Full backend lint, format, and tests; Alembic offline generation; Compose validation; frontend lint/tests/build were executed by the Worker per mission gate, with exact outcomes and skips recorded. The independent Tester could not rerun backend/Compose commands; this limitation is recorded, and skipped PostgreSQL tests are not counted as passes.
- [x] No forbidden product files or external state changes occurred; coordinator ledger/open-question evidence updates are separately recorded.
- [x] Independent read-only Tester evidence and separate Reviewer verdict are recorded. Missing CI run evidence stays `NOT_VERIFIED` and blocks task completion.

## Verification commands

From `backend/` (existing repository/workflow commands):

1. `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py`
2. `.venv\Scripts\ruff.exe check .`
3. `.venv\Scripts\ruff.exe format --check .`
4. `.venv\Scripts\python.exe -m pytest -q`
5. `.venv\Scripts\python.exe -m alembic upgrade head --sql`

From repository root:

6. `docker compose --env-file .env.example config --quiet` (only if the repository's placeholder-based command is valid in this environment; do not add secret values to files or output)
7. `npm --prefix frontend run lint`
8. `npm --prefix frontend run test -- --run`
9. `npm --prefix frontend run build`
10. `git diff --check`

Windows job must execute the exact focused test selector recorded in the workflow. Linux full backend tests must run with the configured PostgreSQL service; report actual test count and all skips. Run CI-equivalent remote checks only after a real run exists for the candidate SHA.

## Prompt template

- Library: prompts.chat through installed `.agents/skills/prompt-lookup`.
- Real template searched and retrieved for this task: **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Modernized Worker prompt: “Act as the CHPMIS-020 backend Worker. First add a regression through the production `WindowsRegistryBackend.read_trusted_keys()` path using mocked Win32 APIs and a valid synthetic Ed25519 key containing `0x80` and `0xff`; run it RED before implementation. Separate the non-Windows fail-closed guard from platform-specific mocked Win32 tests. Make the smallest bounded unsigned/bounded-byte conversion fix, preserve the fixed trust source and all fail-closed/cleanup behavior, and add a Windows CI job that actually runs the Win32 mock tests. Do not touch real Registry state, secrets, identities, ACLs, schema, auth policy, or files outside the four-file allowlist. Run only the listed repository checks, report exact outputs, exits, skips and why each skip is covered, then request an independent read-only Tester and separate Reviewer. Do not commit or push.”

## Definition of Done

- Product/test/workflow scope is respected and the new test proves exact 32-byte preservation through the production reader path.
- Linux guard and Windows internal coverage are clearly separated; Windows CI coverage is configured and observed when a run exists.
- Assigned local checks and independent Tester/Reviewer evidence are recorded exactly; unobserved remote CI is `NOT_VERIFIED`.
- `.team/ledger.md` is updated with only observed harness/model/provider/profile/effort details.

## Independent Verification Status

- Full Tester and Reviewer records: `.team/tasks/CHPMIS-020-opencode-verification.md`.
- OpenCode Tester: `blocked` — backend venv, Ruff, Alembic and Docker commands were denied; frontend and diff checks passed. No bypass attempted.
- OpenCode Reviewer: `APPROVE`, no blocking findings. The Worker’s `[x]` statement that Windows CI ran is stronger than observed evidence; this task pack leaves the corresponding CI checkbox open.
- Coordinator read-only follow-up: 6 Windows/Win32 selector tests and all 45 tests in `test_admin_bootstrap.py` passed; Alembic offline generation, Compose validation, and `git diff --check` passed. Full backend pytest (140 passed, 6 skipped, 16 setup errors) and Ruff format check (exit 1) were limited by filesystem access denials; this is not independent Tester evidence. Exact commands and results are recorded in `.team/tasks/CHPMIS-020-opencode-verification.md`.
- Closure: keep `IN_PROGRESS` until a real CI run is observed for the candidate revision and backend evidence is independently verified or explicitly accepted as Worker-only evidence by the owner.

## Hermes card closing contract

ROLE: worker (backend implementation). Work only in this task's workspace. Keep Worker, OpenCode Tester, and Hermes Reviewer serialized. Finish with exactly one of `kanban_request_review(summary=...)`, `kanban_block(reason=...)`, or `kanban_complete(result=...)`; include changed files, RED/GREEN evidence, exact commands/results/exits, skip coverage, requirement trace, and remaining limits. Do not stage, commit, or push.

## Coordinator GitHub Actions follow-up — 2026-11-05

- GitHub connector confirmed the existing repository `Kudo15/CHANH-HUNG-PMIS` has branch `audit-remediation/verify-audit-findings` at the local baseline SHA `f13fb67d037c4f4c1552da82c04b5c0e60af5d5a`. Local `git remote -v` remains empty; no local remote was added.
- Actions run `41419921117` (#3, event `push`, exact baseline SHA) completed with failure. Frontend job `125192726654` passed. Backend job `125192726890` failed in pytest: `test_windows_registry_backend_null_pointers_and_cleanup_on_error` reached the production non-Windows guard on Ubuntu; result **1 failed, 156 passed, 2 skipped**, exit 1. Ruff check and format had passed; Alembic and Compose steps were skipped after pytest failed.
- This reproduces the platform-separation defect on the baseline commit. The current working tree changes add explicit non-Windows skips for Win32 internals, preserve a separate non-Windows guard regression, and add the `windows-backend` job. They are uncommitted and not present at `f13fb67`; no CI result exists for them.
- No workflow rerun was requested because it would execute the same baseline SHA; no remote ref or repo content was changed. Under the repository's no-commit/no-push boundary, AC-04 and CHPMIS-020 remain NOT_VERIFIED / IN_PROGRESS until the owner-controlled normal publication process exposes the exact candidate SHA and CI runs on it.
