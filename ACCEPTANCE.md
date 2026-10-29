# Acceptance Criteria — First Vertical Slice

All criteria start `NOT_STARTED`. A criterion becomes `PASS` only after its specified evidence exists and an independent reviewer accepts the result. Policy-dependent criteria remain blocked until their Human Gate is approved.

| ID | Acceptance criterion | Planned evidence | Status |
|---|---|---|---|
| AC-01 | Developer can start the synthetic-data stack locally with Docker Compose; all published ports bind to `127.0.0.1` | `docker compose config`, `docker compose up` output and listener/bind inspection | NOT_STARTED |
| AC-02 | API liveness and readiness endpoints distinguish process from database readiness | Backend tests and HTTP response evidence | NOT_STARTED |
| AC-03 | Alembic migration applies to an empty PostgreSQL database and schema can be inspected | Migration command output and migration tests | NOT_STARTED — Human Gate for schema |
| AC-04 | Frontend and backend expose real repeatable test/lint commands and CI runs them without production deployment | CI run URL/logs and local command output | NOT_STARTED |
| AC-05 | Approved user can sign in; unauthenticated/inactive user cannot access protected endpoints | Auth integration tests | NOT_STARTED — Human Gate for identity/session |
| AC-06 | Authorized user can create and read a project with approved minimum fields | API/UI tests and record evidence | NOT_STARTED — Human Gate for project fields |
| AC-07 | Authorized project user can assign staff; unauthorized user cannot | Positive/negative API tests | NOT_STARTED — Human Gate for authorization matrix |
| AC-08 | Authorized participant can create and assign a task within an authorized project | API/UI tests | NOT_STARTED — Human Gate for model/permissions |
| AC-09 | Only approved task state transitions are accepted; invalid transitions are rejected | Workflow unit/integration tests | NOT_STARTED — Human Gate for workflow |
| AC-10 | Cross-project and cross-department access attempts are denied on reads, writes, and lists | Security integration tests including guessed IDs | NOT_STARTED — Human Gate for scope matrix |
| AC-11 | Dashboard totals/lists only include authorized projects and tasks | API tests with mixed authorized/unauthorized fixtures | NOT_STARTED — Human Gate for scope matrix |
| AC-12 | Create, assignment, and status changes produce audit records with approved fields | Integration tests and audit query evidence | NOT_STARTED — Human Gate for audit policy |
| AC-13 | Authorized reviewer can inspect the relevant audit trail; unauthorized user cannot | Positive/negative audit API tests | NOT_STARTED — Human Gate for audit access |
| AC-14 | E2E path completes sign in → create project → assign staff → task update → dashboard → audit | Playwright result and captured test report | NOT_STARTED — depends on AC-05–13 |
| AC-15 | No real agency data/secrets are in fixtures/Git; external AI access is absent from MVP | Repo secret scan/diff review and config inspection | NOT_STARTED |

## Commands
No project verification commands exist yet. The first foundation task must add scripts and CI, then update this document with their exact command strings. Planned Docker checks above are not evidence until run.
