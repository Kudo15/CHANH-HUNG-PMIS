# CHPMIS-026-R1 — Independent verifier evidence review

## Task identity

- **Role:** OpenCode independent read-only Reviewer.
- **Status:** COMPLETE — APPROVED; 0 P1/P2, 1 P3 metadata wording note, reconciled by Coordinator.
- **Traceability:** CHPMIS-026, CHPMIS-023, CHPMIS-011/012-F2; AC-05/14 preparation only.
- **Required session start:** Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, `.team/tasks/CHPMIS-026-CHPMIS023-compose-config-verification.md`, this task pack, `.team/tasks/CHPMIS-026-verifier-report.md`, `.team/tasks/CHPMIS-023-isolated-synthetic-topology.md`, `.team/tasks/CHPMIS-023-worker-report.md`, `.team/tasks/CHPMIS-023-R1-review.md`, `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`, `docs/MISSION.md`, and `ACCEPTANCE.md`. Report all required reads.

## Objective

Independently determine whether the verifier report accurately distinguishes a shell-policy denial from an executed Compose command, whether run/session metadata are reconciled to the observed role-run record, and whether task/acceptance boundaries remain truthful.

## Scope and boundaries

- Read-only inspection of the required docs, report, and two CHPMIS-023 configuration files.
- Do not run any command, test, Docker/Compose action, service/port check, or provider/host action. Do not inspect credentials, environment values, Registry/accounts/ACLs, or edit files.
- Do not treat a permission denial as evidence about Compose validity. Do not recommend or attempt a wrapper, alternate executable, interpreter, permission change, or retry.
- Do not claim AC-05/AC-14 PASS or approve any runtime or host action.

## Review criteria and DoD

- Confirm task scope, traceability, no-edit/no-runtime boundaries, exact denied command, and absence of a Compose exit code.
- Assess the discrepancy between the verifier's closing text and available run/session IDs; report any metadata/reporting correction needed with file/line and P1/P2/P3.
- Ensure status is BLOCKED/NOT_VERIFIED for the attempted verifier and AC-05/14 remain unchanged.
- Return `APPROVED` or `CHANGES_REQUESTED`, with findings and evidence limits. No review verdict may imply the Compose command ran.

Finish with:

`SUMMARY: <one line>`
`ROLE_RESULT: done|review|blocked`
