# CHPMIS-027-R1 — Independent review report

- **Task/role:** CHPMIS-027-R1, OpenCode independent read-only Reviewer.
- **Run/session:** `2026-11-05T07-22-58-reviewer-chpmis-027-r1-independent-static-review-ac5e`; `ses_e556913b6ffeJeu65fKj0YISoQ`; GUI listed in OpenCode Desktop.
- **Project/service:** `C:/Users/AZAI/Desktop/CHANH HUNG PMIS`; shared service `http://127.0.0.1:28894`.
- **Model/provider/cost:** model not exposed (`-`); provider not exposed; cost USD 0; run output counters: input 363400 / output 8344 / cache-read 2432000. Final role message counters were input 4306 / output 4767 / cache-read 91200 (not session totals).
- **Result:** `APPROVED`; role `ROLE_RESULT: done`; driver exit 0. No commands, E2E, runtime, browser, provider, port, database, or Registry actions.

## Review outcome

- Scope: **PASS** for the four allowlisted CHPMIS-027 paths; dedicated config and mixed UI/API journey met the static pack. Reviewer confirmed the actual OIDC flow, separate PM C/Member D contexts, cookie-attribute-only assertions, in-memory CSRF use, PM C positive actor, safe unauthenticated 401, process-env-only credential names, and no sensitive output/artifacts.
- T1 finding F1: **REJECTED as a static asset defect.** The Reviewer found the binding/session/CSRF cookies are host-only (no `Domain`) for `127.0.0.1`; cookie scope is not port-specific, so a callback at port 28000 and app/proxy requests at 25173 are eligible under the shared host. This is static source/config reasoning, not runtime proof. Secure-cookie behavior on HTTP loopback and browser transport remain runtime prerequisites to verify later.
- Findings: 0 P1, 0 P2, 3 non-blocking P3:
  1. Dashboard counts are asserted after the transition button changes but without an explicit page reload; future gated runtime evidence should demonstrate the refreshed 1/0/0 state.
  2. Audit history fetch limit is 20; the unique project per run mitigates cross-run history concerns, and the isolated DB should be used for gated execution.
  3. Worker report says lint exit 2 while independent T1 observed exit 1; both remain `NOT_VERIFIED` due local dependency corruption and do not prove authored-code correctness.
- Reviewer also records that further unitemized P3s from T1 were not evidenced by its own scoped inspection; no additional findings are adopted without evidence.

## Evidence and limits

T1 exact results remain: lint exit 1 `NOT_VERIFIED`; build exit 1 `NOT_VERIFIED`; `git diff --check` exit 0. The Reviewer did not rerun them. E2E, live OIDC, Secure-cookie behavior, services/ports and AC-14 all remain `NOT_VERIFIED`. This verdict approves CHPMIS-027 static asset authoring only; it does not pass acceptance AC-14.

## Verdict

**APPROVED** — CHPMIS-027 may close for static asset authoring under its DoD. AC-14 remains `NOT_VERIFIED` pending the synthetic role fixture, isolated runtime, owner Human Gate, and gated live journey.

SUMMARY: Independent static review APPROVED with 0 P1/P2 and 3 non-blocking P3 notes; F1 rejected as a static inference error; lint/build, runtime/E2E and AC-14 remain NOT_VERIFIED.
ROLE_RESULT: done
