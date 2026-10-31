# CHPMIS-008 — AC-10 Department Scope Integration Test Design

## Intent

Close the AC-10 evidence gap by proving through the existing FastAPI and SQLite integration-test setup that matching a project's lead department does not grant access without explicit project membership.

## Goals and non-goals

- Add synthetic-data API integration coverage for list/read and write denial, plus scoped dashboard/audit reads.
- Keep the test on the existing approved policy: explicit project membership is required; department alone grants no access.
- Do not modify runtime authorization, route, schema, migration, workflow, or acceptance policy.
- Do not introduce fixtures with real agency data or external services.

## Approaches

1. Add a focused integration case to the existing `backend/tests/test_projects.py` harness. This reuses the local app/database/session helpers and exercises real API routes with one matching-department nonmember. **Selected by the CHPMIS-008 request** because the requested gap is a backend integration test and the file already owns project scope tests.
2. Add a new test module and duplicate the app/session helpers. This gives AC-10 its own file but repeats test infrastructure without improving isolation.
3. Extend only `test_auth_policy.py`. This is smaller but remains a unit-level check and would not close the documented integration-evidence gap.

## Design

In one focused scenario, create a Project Manager, a Member whose synthetic `department` exactly matches a project's synthetic `lead_department_id`, and a task in that project. Do not add the Member to `ProjectMember`. Use that Member's authenticated session to verify that project/task/member/audit reads return only the approved non-disclosing responses, project list/dashboard do not expose the project, and task-status/project-archive writes return 404 with no state or audit mutation.

The test is intentionally regression-only: current authorization code already appears to enforce explicit membership, so a first run may pass. Do not weaken or temporarily mutate product code to manufacture a RED result.

## Constraints and acceptance

- Only `backend/tests/test_projects.py` may change as product/test code.
- Use the repository's existing SQLite-backed FastAPI integration-test helpers and synthetic identifiers.
- Run the focused test and full backend pytest suite using existing repository commands; record exact results and exit codes.
- OpenCode Tester is read-only and runs after Worker; Hermes Reviewer is read-only and runs after Tester.
- AC-10 remains PARTIAL until the independent Tester evidence and Hermes Reviewer verdict support the update.
