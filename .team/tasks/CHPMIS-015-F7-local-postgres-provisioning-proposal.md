# CHPMIS-015-F7 — Local Synthetic PostgreSQL Provisioning Proposal

## Status

**APPROVED by owner on 2026-11-02.** PostgreSQL image `postgres:17-bookworm` was confirmed locally available. One isolated PostgreSQL runtime is running healthy on `127.0.0.1:55432` under a unique Compose project and volume. No product code has been changed under this proposal.

## Why a new path is needed

The F7 test `test_postgresql_distinct_requests_same_target_concurrency` is skipped when `TEST_DATABASE_URL` is absent. Hermes, OpenCode, and Codex Workers each ran the focused test and skipped before edits. The Coordinator found no `TEST_DATABASE_URL` in Process/User/Machine environment scopes and no `.env`, `backend/.env`, `.env.local`, or `backend/.env.local` file. The owner-selected existing-context path therefore has no identified local source yet.

Repository `compose.yaml` already defines a PostgreSQL 17 `db` service bound to `127.0.0.1:5432`, with a named `pgdata` volume and a required synthetic password. `.env.example` contains placeholders, not a usable test URL/password. `docker compose version` reports 5.6.1. The image was later confirmed locally available, so no pull was needed.

## Proposed bounded action

With owner approval, provision a separate local synthetic PostgreSQL runtime for F7:

1. Use only the existing `db` service definition and `postgres:17-bookworm` image; do not start backend, frontend, or Keycloak services. Do not pull/install an image if it is not already available locally.
2. Use a unique Compose project name so Docker creates a separate project-scoped database volume, preserving the existing default `pgdata` volume and every database already on the machine.
3. Bind the new PostgreSQL container to `127.0.0.1:55432` through a temporary Compose override outside tracked product files. Do not probe ports; if Docker reports a bind conflict, stop and request a revised plan.
4. Generate a synthetic, URL-safe PostgreSQL password locally. Pass it only through a short-lived, restrictive local launcher that injects `POSTGRES_PASSWORD` when starting the container and `TEST_DATABASE_URL` into the Codex Worker command environment. Never put credentials in chat, a prompt, repository files, logs, or ledger. The launcher must report only success/failure and must not echo variable values.
5. Run a fresh Codex Worker card. The first test command remains the focused F7 pytest command, invoked by the launcher. If it skips or does not produce the expected live duplicate-grant RED, stop before edits. If it produces RED, proceed within the original two-file scope and exact verification commands.
6. Preserve the isolated container and volume after verification; do not drop databases, remove the volume, or run `down -v`. A later stop/removal decision can be handled separately.

## Approval record

Owner replied “Duyệt phương án cô lập” on 2026-11-02, approving one isolated synthetic PostgreSQL 17 service bound only to `127.0.0.1:55432`, using a new Compose project/volume and a temporary secret-safe launcher to pass context to the Codex Worker. This explicitly expands the earlier F7 instruction that prohibited starting services or using an alternate database source. Product-code scope remains exactly `backend/app/auth/routes.py` and `backend/tests/test_postgresql.py`.

## Execution evidence

- `docker image inspect postgres:17-bookworm --format '{{.Id}}'` → exit 0; image was already local. No pull was run.
- `docker compose --project-name chpmis015f7-201d2b956e --file compose.yaml --file <temporary override> up --pull never --wait --wait-timeout 60 --detach db` → exit 0; unique network/volume and container created, service reported healthy. Override bound only `127.0.0.1:55432`; no other services started. The synthetic password was generated in memory and not recorded.
- Fresh Codex CLI Worker was launched with `TEST_DATABASE_URL` included in the shell environment allowlist. Its exact first command exited 1 before pytest collection: `WinError 10106` importing Python `_overlapped` through the `anyio` pytest plugin. Worker stopped without other commands, reads, or edits.
- Coordinator-owned exact focused command `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target` from `backend/`, with the synthetic loopback context: exit 0, `1 passed, 5 deselected, 2 warnings in 17.61s`. This did not produce the required duplicate-grant RED.
- Result: the first Coordinator run passed, and a bounded read-only follow-up reproduced the expected RED with two HTTP 200 approvals. The existing synchronization hook is timing-dependent; analysis is in `.team/tasks/CHPMIS-015-F7-reproduction-diagnosis.md`. No implementation was authorized in the read-only follow-up, so F7 remains `BLOCKED / NOT_VERIFIED` pending a fresh Worker path. The isolated container and volume are preserved. No password or URL is recorded here.

If this option is declined, the remaining path is for the owner to identify and provision the existing local context source; no credential needs to be sent in chat.
