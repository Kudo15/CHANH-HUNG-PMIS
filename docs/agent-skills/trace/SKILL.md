---
name: trace
description: Use when the user invokes /trace or asks for a compact report of delegated agent runs across harnesses, roles, or models.
---

# Trace Agent Runs

Turn run results already available in the current task into a compact, evidence-based report. Cover any harness (for example OpenCode, DeepSeek Harness, Hermes, or Qoder), role (worker, reviewer, verifier, or another recorded role), and model. This skill reports runs; it does not launch or repeat them.

## Collect facts

Use the current conversation and tool results first. When the user points to a ledger or run artifact and it is accessible, read only the relevant records needed to fill the report. Preserve exact run IDs, session IDs, model IDs, statuses, exit codes, cost, token counts, GUI flags, and verification outputs.

Keep these fields distinct:

- **Harness**: the runner or agent system that dispatched the run, such as opencode, deepseek-harness, or hermes.
- **Role**: the assigned agent role, such as worker, reviewer, or verifier.
- **Model**: the recorded provider/model identifier, such as deepseek/deepseek-flash or gpt-6-luna.

Do not infer one field from another. Use the phrase “không có dữ liệu” for unavailable values; never turn unknown cost or token counts into zero. Do not rerun a billable agent or mutate a workspace to fill a reporting gap.

## Report format

Write in the user's language. Start with a one-line overall result: pass, partial, blocked, or failed, with the main reason. Then use the following tables, omitting only the check matrix when no checks or acceptance criteria were part of the task.

### Checks

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Each requested acceptance check | PASS / FAIL / PARTIAL / UNKNOWN | State the observed evidence and its source |

### Runs

| # | Harness | Role | Model | Trạng thái | Exit | GUI / session |
|---|---|---|---|---:|---:|---|
| One row per run | Recorded harness | Recorded role | Exact model ID | Exact status | Code or — | GUI flag and session title/ID, or unavailable |

### Run details

| # | Run ID | Session ID | Cost (USD) | Tokens (input / output / reasoning) | Summary |
|---|---|---|---:|---:|---|
| One row per run | Exact ID | Exact ID or unavailable | Exact amount or unavailable | Exact counts or unavailable | Concise result and evidence qualification |

### Skills used in this task

| Skill | What it did in this task | Evidence / status |
|---|---|---|
| Skill name | Concrete contribution, such as finding/adapting a prompt template, planning implementation, dispatching a Hermes/OpenCode/DeepSeek role, or producing this trace | Where it is evidenced: conversation, task pack, run record, or skill/tool output |

Include skills actually read, invoked, or applied by the coordinator or delegated roles when the current task's records support that claim. Describe each skill's concrete contribution in this task; do not infer usage from a skill merely being installed, available, or named in a task prompt. If a skill is mentioned but execution is not evidenced, label it `mentioned; use not verified` instead of presenting it as used. If no usage evidence is available, write `không có dữ liệu` rather than assuming no skills were used.

Keep skill names distinct from harnesses, roles, models, and tools. For example, `hermes-role-agents` is a dispatch skill; Hermes is the harness. `opencode-role-agents` and `deepseek-harness-role-agents` are skills; OpenCode and DeepSeek Harness are harnesses. Explain the skills' purposes, not just their names.

Typical contributions include `prompt-lookup` finding and adapting a task prompt; `superpowers:brainstorming` clarifying the approach; `superpowers:writing-plans` turning requirements into an implementation plan; `hermes-role-agents`, `opencode-role-agents`, or `deepseek-harness-role-agents` dispatching and collecting work from their respective harnesses; and `trace` compiling the run evidence. Include only the skills supported by this task's evidence.

After the tables, add only applicable details:

- **Cost/tokens total:** Sum known costs and token counts. Label totals partial when one or more runs lack those metrics; never imply missing values are zero.
- **Exact status output:** Include verbatim when captured or explicitly requested. Do not reconstruct it from a summary.
- **Workspace / GUI:** State the project path and visibility evidence when available. For Git status/diff, report results only when the directory is a Git repository and those checks were run; otherwise say it is not a Git repository or not checked.
- **Deviations / limitations:** Name deviations from the requested procedure or applicable skill, and cite the observed message. If none, say “Không có sai lệch được ghi nhận.”

## Evidence rules

- Separate what a run or agent **reported** from what was independently **verified**. For example: Reviewer reported the write was denied; probe-file absence was independently verified.
- Mark each check PASS only when its required evidence is present. Use PARTIAL, UNKNOWN, BLOCKED, or FAIL as appropriate; do not convert a run's done status into proof that every acceptance check passed. For a permission-denial check, mark PASS only when recorded tool or permission output confirms the denial; if only the agent reports denial and the probe file is absent, mark PARTIAL because absence proves no file remains, not why.
- Claim GUI visibility only from an explicit gui_visible: true/listed result or user confirmation. A session ID alone does not establish GUI visibility.
- Preserve relevant errors and exit codes. For a failed run, include its recorded error or stderr excerpt when available; do not invent a cause.
- Include the ledger/run-artifact location when available and useful for reopening or auditing the result.
- Never expose credentials, tokens used for authentication, or unrelated private data while inspecting records.

## Example

| # | Harness | Role | Model | Trạng thái | Exit | GUI / session |
|---|---|---|---|---|---:|---|
| 1 | opencode | worker | deepseek/deepseek-flash | done | 0 | true · ses-A |
| 2 | hermes | verifier | gpt-6-luna | blocked | 4 | không có dữ liệu |

| # | Run ID | Session ID | Cost (USD) | Tokens (input / output / reasoning) | Summary |
|---|---|---|---:|---:|---|
| 1 | run-A | ses-A | 0.0005 | 1,111 / 451 / 18 | File creation independently verified |
| 2 | run-B | không có dữ liệu | không có dữ liệu | không có dữ liệu | Blocked pending approval

