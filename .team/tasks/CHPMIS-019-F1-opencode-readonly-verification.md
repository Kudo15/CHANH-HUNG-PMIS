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

## Retry — 2026-11-03

- Run `2026-11-03T04-42-09-verifier-chpmis-019-f1-independent-verification-r-66b1`, session `ses_e60490b6bffejdnQV8KHtiR3S0`, GUI listed, service `http://127.0.0.1:28894`, role result `review`, driver exit 1 (CLI exit 0); model not exposed, cost 0, tokens input 103855 / output 3085 / cache-read 153600.
- From repository root: `npm --prefix frontend run test -- --run src/ProjectWorkbench.test.tsx` → 13 passed, exit 0; `npm --prefix frontend run test -- --run` → 26 passed, exit 0; `npm --prefix frontend run lint` → exit 0; `npm --prefix frontend run build` → exit 0. Verifier also inspected safe validation-error formatting and deferred project-switch race guards.
- The assigned scoped `git diff --check` was denied before execution by shell policy twice; verifier also reports a denied `git ls-files` probe. The command is **NOT_VERIFIED independently** by this run. Verifier returned `review` rather than the pack's requested `blocked` result when a shell command cannot execute; do not treat the role result as completion. No permission rule was changed.
- Coordinator separately ran the exact scoped `git diff --check` from repository root: empty output, exit 0. The earlier independent Hermes Reviewer also ran it and approved the implementation, but neither result is an OpenCode execution. Task remains IN REVIEW under its existing closure rule.
- Session-start compliance: the OpenCode role's recorded output does not show a read of `.team/CHARTER.md` or `docs/MISSION.md`. These required reads are NOT_VERIFIED for this session; observed test outputs remain evidence, but the omission must be considered before closure.
- Owner decision, 2026-11-03: selected **“Chấp nhận bằng chứng thay thế”** for the scoped diff check only: accept Coordinator's exact command (empty output, exit 0) together with the existing independent review, while recording the OpenCode denial accurately. This does not assert OpenCode ran the command. CHPMIS-022 fresh evidence review remains pending for session-start compliance concerns.
- CHPMIS-022's same OpenCode session completed after its driver timeout: fresh Reviewer read the required project session documents and approved the narrow evidence, confirming the four test/build/lint outputs and the denied diff in the source logs. It identified P2 for the original verifier's missing session-start reads; that historical process gap remains recorded. The fresh review addresses the evidence assessment, not the original session's compliance. With the owner's explicit substitution for the one denied diff command and existing independent code review, CHPMIS-019-F1 is COMPLETE. Full record: `.team/tasks/CHPMIS-022-verifier-evidence-review.md`.

## OpenCode closing contract

Return exactly:

```text
SUMMARY: <one line with exact check results or blocker>
ROLE_RESULT: <done|review|blocked>
```
