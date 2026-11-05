# CHPMIS-018-F1-T1 — Proposed OpenCode Retry Environment

## Status and decision

**NOT AUTHORIZED / OWNER CHOSE T1 BLOCKED.** The owner chose to keep T1 blocked instead of authorizing this proposed exception. This document remains a record of the proposal; it does not authorize changing OpenCode permissions, starting a service, accessing credentials, or dispatching T1.

## Evidence

- T1's first OpenCode verifier run was blocked: all four assigned commands were denied before execution, and its PostgreSQL context was absent. Live RED remains `NOT_VERIFIED` independently.
- The existing synthetic container `chpmis-gate-20261101-db-1` is healthy and published at `127.0.0.1:5432`. Its credentials are not available as process-local settings; they were not inspected or printed.
- The local `postgres:17-bookworm` image exists. No image pull is required for the proposed service.
- OpenCode diagnostic DIAG1 confirmed that a harmless environment marker supplied to the dispatch process reached the verifier shell (`PRESENT`, exit 0). It did not access PostgreSQL or verify T1.
- `.venv\Scripts\python.exe` and `.venv\Scripts\ruff.exe` exist in `backend/`.

## Recommended scoped exception

1. Create one **task-specific OpenCode verifier agent** for CHPMIS-018-F1-T1, using the shared desktop service and a new session. Keep `edit: deny` and default shell `deny`; allow only the four exact verification commands already listed in the T1 pack. Use the existing venv executables and working directories. Do not modify the global `role-verifier` or allow wrappers, extra shell commands, or product edits. Invoke through the role driver as `--role verifier --agent <task-specific-agent>` so the run is recorded and visible in OpenCode Desktop.
2. Start a **separate synthetic PostgreSQL 17 container** using the local image with pulling disabled. Bind its published port only to `127.0.0.1` with an available host port. Use a fresh random synthetic password generated in the setup process; keep it out of chat, repository files, agent prompts, and reports. Pass the resulting synthetic `TEST_DATABASE_URL` / `DATABASE_URL` only through the dispatch process environment. Preserve the new container, volume, and databases after the run; do not drop, reset, or clean up any existing or new data.
3. Run the four T1 commands exactly as specified. Record exact outputs and exits, skip count, new synthetic database name, and preservation evidence without connection strings or credentials. The focused pytest exit 1 with both transitions accepted can be expected RED evidence; it must never be reported as a passing test. A skip or command denial is `NOT_VERIFIED`.
4. Record the OpenCode run, results, and limitations in the task pack and ledger. Preserve the existing R2 Reviewer verdict; re-review if the new Tester finds a defect in the test or report. Do not implement a product fix or commit.

The new service would independently reproduce the condition on a fresh synthetic PostgreSQL instance. It would not independently re-query the six databases in the prior Worker report. OpenCode's command-pattern permissions are not a filesystem sandbox: the authorized pytest can create the intended synthetic database and test artifacts.

## Authorization required

- The current T1 pack says: “Do not change or bypass role permissions” and “Never ... start services.” The proposed task-specific verifier and new local container require the owner to explicitly authorize this scoped change to the T1 pack.
- The OpenCode role-agent skill says: “Never try to bypass an agent deny rule or a permission denial. Fix the cause or report blocked.” Creating a new agent which allows commands denied to `role-verifier` would be an explicit exception to that skill instruction; the owner must specifically authorize it.
- No authorization here covers changes to product code, product authentication or authorization, business workflow, remote systems, production, deployments, pushes, database cleanup, or secrets outside the synthetic test environment.

## Alternative

Keep T1 blocked until an already permitted OpenCode verifier environment with the required process-local synthetic PostgreSQL settings is provided. The existing Worker live evidence and R2 static review remain available, and independent live evidence remains `NOT_VERIFIED`.
