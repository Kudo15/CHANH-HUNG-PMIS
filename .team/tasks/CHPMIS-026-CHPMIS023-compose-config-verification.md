# CHPMIS-026 — CHPMIS-023 Compose configuration verification

## Task identity

- **Role:** OpenCode read-only Tester/Verifier; Coordinator tracks evidence; independent Reviewer records a separate verdict.
- **Traceability:** CHPMIS-023; CHPMIS-011/012-F2; AC-05/14 preparation only; `docs/MISSION.md` §5–6.
- **Status:** COMPLETE for bounded evidence reconciliation — Verifier BLOCKED because shell policy rejected the sole command before execution; independent Reviewer APPROVED (0 P1/P2, 1 P3). Compose config rendering remains NOT_VERIFIED. This task is independent of AC-04/CHPMIS-020.
- **Required session start:** Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this task pack, `.team/tasks/CHPMIS-023-isolated-synthetic-topology.md`, `.team/tasks/CHPMIS-023-worker-report.md`, `.team/tasks/CHPMIS-023-R1-review.md`, `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`, `.team/tasks/CHPMIS-011-runtime-approval-proposal.md`, `.team/tasks/CHPMIS-011-runtime-candidate-r2-review.md`, `docs/MISSION.md`, `ACCEPTANCE.md`, `dev/keycloak/compose.chpmis011-isolated.yaml`, and `dev/keycloak/realm.chpmis011-isolated.json`. Confirm the old CHPMIS-011 runbook remains DO NOT EXECUTE. Report every required read.

## Objective

Independently determine whether Docker Compose can render the already-reviewed standalone synthetic topology using the exact command authorized by CHPMIS-023. This is configuration parsing only. It must not start, build, pull, inspect, stop, or connect to a service or provider.

## Scope and hard boundaries

- Read only the task/docs/config paths listed above and inspect `git status --short` / scoped diff for context.
- Run only the exact command below, once, from repository root. The `.env.example` file is the only env file. Do not print or inspect its values. Supply only obviously synthetic process-local values for the two required PM/member password placeholders if they are absent; never persist them or place credentials in task output. Do not inspect any other environment variable or `.env` file.
- If the exact command is denied, Docker/Compose unavailable, a placeholder cannot be safely provided, or rendering requires a different command, stop and report `BLOCKED`/`NOT_VERIFIED` with the exact observed reason. Do not try another executable, shell, wrapper, interpreter, permission change, alternate env file, or service action.
- No service lifecycle, port/host probing, image pull/build, credentials/Registry/account/ACL inspection, provider access/login, tests, code/config/docs edits, commit, push, deploy, or permission changes.
- Existing working-tree changes and resources must remain untouched.

## Sole allowed verification command

From the repository root:

`docker compose --env-file .env.example -f dev/keycloak/compose.chpmis011-isolated.yaml --project-name chpmis023config --profile local-oidc config --quiet`

Use only the synthetic process-local PM/member password placeholders described above; never echo values. Record the exact command, output summary, exit code, and whether any requirement caused a stop. No other command is authorized for verification.

## Reporting format

Report required reads, initial status/diff inspection, exact command and exit code (or `NOT_RUN`), sanitized output summary, any deviation/stop reason, and the result for config rendering. Explicitly state that rendering does not prove ports are free, services start, live OIDC works, bootstrap succeeds, host Registry controls are safe, or AC-05/AC-14 pass. Finish with:

`SUMMARY: <one line>`
`ROLE_RESULT: done|review|blocked`

## Independent review

After the Verifier result, an independent read-only Reviewer checks this pack, the verifier evidence, and the existing CHPMIS-023 config/review. Reviewer must not rerun commands or edit files. Verdict is `APPROVED` or `CHANGES_REQUESTED`, with findings cited by file/line and priority. An approved config-rendering result closes only this verification task; it does not change AC-05/AC-14 or authorize runtime actions.

## Definition of Done

- The exact allowed command was run once and its exit/output are recorded, or a truthful `BLOCKED`/`NOT_VERIFIED` result explains why it could not run.
- Independent Reviewer verdict and run/session metadata are recorded.
- No prohibited action or edit occurred.
- Coordinator updates `.team/ledger.md` and relevant task status only from observed evidence; AC-05/AC-14 remain NOT_VERIFIED.
