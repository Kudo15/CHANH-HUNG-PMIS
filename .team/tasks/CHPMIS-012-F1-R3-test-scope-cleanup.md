# CHPMIS-012-F1-R3 — Test-scope cleanup and final evidence

- **Task ID:** CHPMIS-012-F1-R3
- **Role:** Hermes Worker (test-only implementation)
- **Status:** READY_FOR_WORKER — narrow correction to R2
- **Requirement trace:** CHPMIS-012 / mission §5; AC-05; `AGENTS.md`; `.team/CHARTER.md`; original approved F1 pack `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; R2 follow-up pack `.team/tasks/CHPMIS-012-F1-R2-atomic-consumption-cookie-cleanup.md`.
- **Prompt template:** Real prompts.chat Feature coding template by Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved via `.agents/skills/prompt-lookup` and cited in `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`. Modernized for this cleanup: preserve the positive verifier propagation regression, remove only the unrequested omission case, preserve implementation, and run only the exact checks listed below.
- **Preceding state:** R2 Worker card `t_85bc0983` / run 112 submitted for review. Its atomic-claim and route cookie-cleanup implementation is present. The positive verifier request-body assertion is required; a `code_verifier=None` omission subcase is outside the approved follow-up pack and must be removed. Preserve all other files and pre-existing dirty work.

## Objective

Make one test-only scope correction after R2:

- In `backend/tests/test_auth_oidc.py`, keep `test_default_oidc_client_token_request_body_carries_code_verifier` and its positive assertion for the supplied verifier.
- Remove only the optional `code_verifier=None` omission subcase from that test. Do not change `DefaultOIDCClient`, any other auth tests, or product implementation.
- Append a correction to `.team/tasks/CHPMIS-012-F1-R2-worker-report.md` recording the exact command/CWD deviations and that the coordinator normalized only its own ledger line ending; the exact root `git diff --check` then passed with exit 0. Do not rewrite or erase the R2 report.

## Allowed files

Modify only:

- `backend/tests/test_auth_oidc.py`
- Append-only `.team/tasks/CHPMIS-012-F1-R2-worker-report.md`

No source, route, model, config, migration, other test, task, ledger, frontend, Compose, Keycloak, or unrelated file changes.

## Verification

From `backend/`:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
2. `.venv\Scripts\ruff.exe check . ../dev`
3. `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py tests/test_auth_oidc.py`

From repository root:

4. `git diff --check`

Use exactly these commands and working directories. Do not use alternate path/CWD variants, run mutating formatters, or inspect environment variables. Report the prior R2 full-backend pytest result as historical evidence, not as a fresh R3 run. If any listed check fails, report exact output and do not repair outside the two-file allowlist.

## Definition of Done

- The positive verifier assertion remains; only the `None` omission subcase is removed.
- No product source code changes occur in R3.
- The R2 report gets an append-only correction; all command variants and the final coordinator diff-check pass are represented truthfully.
- All listed R3 commands are reported separately with exact command, CWD, summary, and exit code.
- No commit, stage, push, deploy, secret exposure, or forbidden Git discard command.
