# CHPMIS-015-F7 — Read-only reproduction diagnosis

## Authorization and scope

- Owner authorized a read-only follow-up, up to five invocations of the exact focused PostgreSQL test, to diagnose why the Coordinator's live run passed instead of producing the expected duplicate-grant RED.
- No product-code or test-code edits are allowed. Tests may create only the fresh synthetic databases that the existing test creates from `TEST_DATABASE_URL`; preserve every database and the isolated Compose volume.
- Read scope: the F6/F7 task evidence, `backend/tests/test_postgresql.py`, and the relevant approval transaction in `backend/app/auth/routes.py`.
- Do not inspect, print, or search for environment values; use only the already approved short-lived launcher to inject the isolated synthetic connection context. Do not run host or port diagnostics.
- Test command, from `backend/`: `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target`
- Stop after five invocations or after sufficient evidence identifies whether the race reproduces. Record each output and exit code. Do not edit or dispatch an implementation Worker under this diagnostic authorization.

## Prior evidence

- F6's original Worker reported the focused case failed with two successful approvals. Its preserved synthetic databases contained two canonical active roles and two approved requests for the same target.
- The new isolated F7 PostgreSQL runtime is healthy on loopback port `55432`. The Codex CLI Worker stopped before pytest execution because Python raised `WinError 10106` importing `_overlapped` through `anyio`.
- A Coordinator run of the exact focused test against the isolated runtime passed: `1 passed, 5 deselected, 2 warnings` (exit 0).

## Initial read-only code observations

- The approval route locks the request row with `with_for_update()` but the target-user lookup is a plain query before checking `existing_grant`; no target-user row lock is present in the current source diff.
- The test's SQLAlchemy event hook waits at `before_cursor_execute` when it identifies the target's `user_roles` query. It catches `BrokenBarrierError` and continues without recording whether both threads successfully met at the barrier. This may allow a run to pass without proving both SELECT snapshots observed the empty role state; verify against repeated live outcomes before making a conclusion.

## Outcome

- A second Coordinator-owned exact focused test run produced the expected live RED: `1 failed, 5 deselected, 2 warnings in 6.05s`, exit 1. The assertion output contained two distinct approval requests both returning HTTP 200. This is within the owner's read-only diagnostic authorization; no code was changed.
- Together with the preceding live pass (`1 passed, 5 deselected`), this confirms the race is nondeterministic under the current hook.
- Root cause: the test's `before_cursor_execute` barrier synchronizes threads before issuing the target-role SELECT, but does not guarantee both SQL snapshots were taken before either transaction inserts/commits. It also swallows `BrokenBarrierError`, so a run may pass without evidence that both threads met at the barrier. The route still has only request-row locking; the target `User` lookup is not locked.
- A separate no-secret Codex CLI smoke check ran `.venv/Scripts/python.exe -c "import _overlapped; print(\"OVERLAPPED_IMPORT_OK\")"` from `backend/` under `--sandbox workspace-write` with the same environment filter. It exited 1 with `OSError: [WinError 10106]` before any database access. This supports an inference that the Codex Windows sandbox/runtime cannot initialize the Winsock provider required by Python; the PostgreSQL URL and pytest fixture are not involved in this import failure.
- Recommendation: create a separately scoped test-harness task to make the pre-fix race reproducible while remaining compatible with the approved target-row lock after the fix. A reviewer should validate any synchronization design against both the unfixed and fixed transaction ordering. Do not simply move the barrier to `after_cursor_execute` without proving the fixed path cannot deadlock or fail its test.
- Worker-path result: the owner approved one temporary per-run `sandbox_workspace_write.network_access=true` override while retaining `--sandbox workspace-write` and without changing persistent configuration. A fresh Codex Worker reran the exact focused command first; it still exited 1 during plugin import with `OSError: [WinError 10106]` importing `_overlapped` through `anyio`, before pytest collection or database access. The Worker stopped without additional commands, reads, or edits. The override did not resolve the failure. Do not escalate to full-access mode.
- Result: the underlying defect is confirmed by Coordinator evidence, but the Codex Worker still cannot execute pytest under the approved workspace sandbox, including with the temporary network override. No product code was changed. CHPMIS-015-F7 remains `BLOCKED / NOT_VERIFIED`; a fresh Worker run would need explicit approval to use the Coordinator-captured live RED as its gate evidence, with the Worker operating only within the approved two-file scope and Coordinator performing live verification.
