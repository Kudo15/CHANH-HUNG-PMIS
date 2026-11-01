# CHPMIS-014 — Hermes Independent Reviewer Contract

Role: independent read-only Reviewer. Review the task pack, Worker report, and implementation diff. Do not edit, format, stage, or commit.

Review correctness and scope for canonical role persistence, canonical-plus-legacy zero-admin guard, no legacy conversion/elevation, generated synthetic test keys, bootstrap → session → protected HTTP endpoint coverage, transaction behavior, and whether the tests actually demonstrate the intended finding. Check only the three allowlisted product/test files plus the append-only Worker report; distinguish Coordinator documentation from Worker changes.

Worker reported RED→GREEN, focused tests 18 passed, full backend 100 passed/1 skipped, Ruff check/format PASS, and `git diff --check` PASS. Coordinator independently reran the four backend commands with those same counts and exit 0, plus `git diff --check` exit 0. PostgreSQL remains NOT_VERIFIED (`TEST_DATABASE_URL` unset); do not infer it from SQLite.

OpenCode Tester run `2026-10-31T13-01-14-verifier-verifier-chpmis-014-canonical-bootstrap--e7ac` is BLOCKED: its export records `permission.rejected: Permission denied: shell` and failed PowerShell `&&` parsing. It did not provide valid independent test evidence. Do not treat this as a pass or try to change OpenCode permissions.

Return an evidence-based verdict with concrete file/line findings and limits. Accept or request changes only for this scoped implementation. Preserve the task as incomplete if the OpenCode Tester evidence is a required gate.
