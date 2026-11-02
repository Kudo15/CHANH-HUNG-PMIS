# CHPMIS-013-F1 OpenCode Read-Only Checks

- **Task ID:** CHPMIS-013-F1-T1
- **Role:** OpenCode Tester (read-only)
- **Status:** NOT_VERIFIED — run created a session but ended failed after approximately ten minutes without a verifier result.
- **Scope:** Independently run the exact F1 verification commands from `.team/tasks/CHPMIS-013-F1-current-head-schema-gate.md` against the live task-specific synthetic PostgreSQL service. Do not edit or clean up files, containers, databases, or volumes.
- **DoD:** Set `TEST_DATABASE_URL` and `DATABASE_URL` in the verifier process to the task's synthetic loopback database URL (`postgresql+psycopg://pmis_test:synthetic_ci_only@127.0.0.1:5432/pmis_test`). Report exact commands, outputs, exits, skip status, PostgreSQL server version, and task-specific database names. Keep the synthetic runtime and databases preserved.
- **Requirement trace:** `.team/tasks/CHPMIS-013-F1-current-head-schema-gate.md`, mission §3 Priority 1.
- **Prompt template:** Not applicable; Tester task, no implementation work.
- **Evidence:** Run `2026-11-01T15:05:12.684Z-verifier-chpmis-013-f1-read-only-gate-verificatio-f90f`; final role-run ledger metadata records status `failed`, session `ses_e685b5734ffeai6y5jaJnR7zg0`, GUI listed, and no summary. After approximately ten minutes without a verifier result, the exact `opencode-cli` process was terminated. Driver exited 1 (`opencode exited 4294967295`). This is not a pass. No session export or raw logs were read.
