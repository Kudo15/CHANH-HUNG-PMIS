# CHPMIS-019-F1 — Coordinator Verification Evidence

- **Task ID:** CHPMIS-019-F1
- **Role:** Coordinator
- **Status:** IN REVIEW — local gates and Hermes review pass; OpenCode read-only verification is NOT_VERIFIED.
- **Worker:** Hermes card `t_930129a8`, session `20261101_230044_cd684c`.
- **Reviewer:** Hermes card `t_281989f0`, run #100, session `20261101_232016_96518d`, APPROVED (0 P1/P2/P3).
- **OpenCode:** Run `2026-11-01T16-16-21-verifier-chpmis-019-f1-read-only-verification-898e`, session `ses_e681a3184ffe6nLLfacjNayPeB`, final status failed before checks because no usable default provider key; NOT_VERIFIED.

## Worker changes

Worker changed only the four allowlisted frontend source/test files and appended `.team/tasks/CHPMIS-019-F1-worker-report.md`:

- `frontend/src/lib/apiError.ts`: formatter returns safe display text from string and FastAPI/Pydantic location/message fields, falls back on malformed shapes, and excludes `input`.
- `frontend/src/components/ProjectWorkbench.tsx`: ignores late mutation refresh and audit-pagination results after project selection changes; uses the formatter in mutation errors.
- `frontend/src/ProjectWorkbench.test.tsx` and `frontend/src/lib/apiError.test.ts`: regression coverage for array/object/malformed details and deferred A-to-B refresh/pagination races.

No backend, auth-state, workflow, due-date, PM membership, dependency, or unrelated UI files changed.

## Coordinator verification

Working directory: repository root `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`.

| Command | Result |
|---|---|
| `npm --prefix frontend run test -- --run src/ProjectWorkbench.test.tsx` (restricted attempt) | Exit 1 before test execution: Vite native Tailwind binding could not load; `spawn EPERM`. |
| Same focused command under reviewed execution | 13 passed, 1 file passed; exit 0. |
| `npm --prefix frontend run test -- --run` | 26 passed across 3 files; exit 0. |
| `npm --prefix frontend run lint` | ESLint completed with 0 errors/0 warnings; exit 0. |
| `npm --prefix frontend run build` | TypeScript and Vite production build passed; exit 0. |
| `git diff --check -- frontend/src/components/ProjectWorkbench.tsx frontend/src/ProjectWorkbench.test.tsx frontend/src/lib/apiError.ts frontend/src/lib/apiError.test.ts .team/tasks/CHPMIS-019-F1-worker-report.md` | Clean; exit 0. |

Reviewer independently reran the focused/full tests, lint, build, and diff check and approved with 0 findings. OpenCode run metadata shows default route only (`model_requested=null`, `model_used=null`), cost USD 0, GUI-visible session; the driver reported no usable model/provider key (rate-limited/on cooldown), exit 1, and no checks ran. No alternate model or permission changes were attempted.

## Remaining scope

The overall CHPMIS-019-F1 DoD remains open until OpenCode can perform its required read-only checks through the configured route. Separate open questions remain for 401/403/logout stale-state behavior, PM/membership consistency, and due-date timezone semantics; this task intentionally did not change them.
