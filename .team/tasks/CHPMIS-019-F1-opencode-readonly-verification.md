# CHPMIS-019-F1-T1 — OpenCode Read-Only Verification

- **Task ID:** CHPMIS-019-F1-T1
- **Role:** OpenCode Tester / Verifier (read-only)
- **Status:** NOT_VERIFIED — the shared OpenCode route had no usable model provider key (rate-limited/on cooldown); no verification commands ran.
- **Scope:** Independently inspect and verify the final CHPMIS-019-F1 allowlist: `frontend/src/components/ProjectWorkbench.tsx`, `frontend/src/ProjectWorkbench.test.tsx`, `frontend/src/lib/apiError.ts`, and `frontend/src/lib/apiError.test.ts`. Do not edit files.
- **Definition of Done:** Rerun the exact frontend checks below; confirm 422 array/object details render only trusted text and late project A refresh/pagination results cannot update project B; report exact outputs/exits and any limitations.
- **Requirement trace:** `.team/tasks/CHPMIS-019-F1-frontend-stale-response-and-validation-errors.md`, mission §6.
- **Prompt template:** Not applicable; read-only verifier.

## Commands

- `npm --prefix frontend run test -- --run src/ProjectWorkbench.test.tsx`
- `npm --prefix frontend run test -- --run`
- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`
- `git diff --check -- frontend/src/components/ProjectWorkbench.tsx frontend/src/ProjectWorkbench.test.tsx frontend/src/lib/apiError.ts frontend/src/lib/apiError.test.ts .team/tasks/CHPMIS-019-F1-worker-report.md`

Use the configured OpenCode default model with no override. Preserve all files and runtime. If the read-only role cannot execute shell commands, return `ROLE_RESULT: blocked`; do not request weaker permissions or route through another model.

- **Evidence:** Run `2026-11-01T16-16-21-verifier-chpmis-019-f1-read-only-verification-898e`; final ledger metadata status `failed`, session `ses_e681a3184ffe6nLLfacjNayPeB`, GUI listed, `model_requested=null`, `model_used=null`, cost USD 0, driver exit 1, and no role summary. Driver reported no candidate model with a usable provider key; the only route was rate-limited/on cooldown. No checks ran; no alternate model or permission change was used.

## OpenCode closing contract

Return exactly:

```text
SUMMARY: <one line with exact check results or blocker>
ROLE_RESULT: <done|review|blocked>
```
