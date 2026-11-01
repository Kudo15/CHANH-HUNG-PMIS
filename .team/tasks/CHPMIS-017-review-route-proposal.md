# CHPMIS-017 — Proposed Independent Review Route

## Status
APPROVED by owner on 2026-11-01: retain the recorded six OpenCode check results and assign the missing independent source assessment to one Hermes Reviewer. The recorded OpenCode process violations remain NOT_VERIFIED and are not erased by this decision.

## Evidence available
- OpenCode run `2026-11-01T12-21-05-verifier-chpmis-017-scoped-independent-authorizat-fe0e` ran all six required checks with exit 0. Its combined diff was truncated and it attempted an unlisted denied echo.
- OpenCode follow-up `2026-11-01T12-26-57-verifier-chpmis-017-independent-source-review-fol-eba2` read the matrix, Worker report, and all seven individual diffs without truncation, but ran unlisted hash commands after a denial and gave no criterion-by-criterion assessment.
- The Coordinator's pre- and post-follow-up SHA-256 comparisons match all seven hashes in `.team/tasks/CHPMIS-017-verifier-source-followup.md`. The prior six checks are evidence for those seven files, subject to checking the hashes again before and after any review.

## Owner decision
Accept the six recorded OpenCode check results as test evidence despite the documented verifier process violations; authorize one independent Hermes Reviewer to perform the complete criterion-by-criterion source and security review that remains missing. This reviewer is independent of the implementing Hermes Worker and must not change code. Its review must explicitly assess the owner-approved role intersection and every route/role/scope criterion in the main task pack, inspect each of the seven diffs individually, cite findings with file and line, and report APPROVED or CHANGES_REQUESTED. The Coordinator must confirm that all seven source hashes still match the tested baseline before and after review.

Approval of this route would amend only the CHPMIS-017 review sequencing and evidence criterion: the independent Hermes Reviewer supplies the missing source assessment; the exact OpenCode outputs remain the test evidence, while both OpenCode process deviations remain recorded. It does not approve any new authorization policy, source change, deployment, or release.

## Alternative
Keep the current route and authorize a new tightly scoped OpenCode source-review run; no task completion can be claimed until that run meets its pack and a separate Hermes Reviewer approves.

## Limits
Repository-wide Ruff has 14 separately tracked findings outside CHPMIS-017 scope; remote CI, actual IdP, and live database/runtime evidence remain NOT_VERIFIED where already stated in the main task pack. The owner authorized the single independent Reviewer under this route; no new product-code change, deployment, or release is authorized.
