# CHPMIS-017-L1 — Repository Ruff I001 Backlog

## Status and scope
BACKLOG, tracking only. Owner chose to keep these findings outside the CHPMIS-017 allowlist; no Worker dispatch or product-file change is authorized by this record. Plan a separately scoped task with real prompt template and required checks before implementation.

## Evidence
OpenCode run `2026-11-01T05-39-48-verifier-chpmis-017-corrected-independent-verific-ad39` reported 19 Ruff I001 findings repository-wide, five of which were addressed within CHPMIS-017-T2. Fourteen were outside scope: one each in Alembic revisions `0002`–`0006` (five findings) and nine findings across eight test modules: `test_admin_bootstrap.py`, `test_audit_atomicity.py`, `test_auth_oidc.py`, `test_auth_remediation.py` (two), `test_auth_session.py`, `test_health.py`, `test_oidc_client.py`, `test_postgresql.py`. Counts are from that historical run; current repository-wide status has not been rerun for this backlog.

## Future definition of done
Reconfirm the current repository-wide findings before editing, agree a bounded file allowlist, fix import ordering without changing behavior, and run the repository's defined Ruff, format and appropriate test checks. Record exact outputs/exit codes and independent review. Do not claim repository-wide Ruff passes until actually verified.
