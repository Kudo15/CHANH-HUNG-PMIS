#!/usr/bin/env node
// Create a Hermes kanban card for a role agent, dispatch it, wait for the outcome, report.
// Stdlib only. Node >= 18.

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const USAGE = `Usage: node hermes-role-task.mjs --title TEXT (--body-file PATH | --body TEXT) [options]

Role
  --role NAME            worker | reviewer | verifier | none   (default: worker)
  --no-role-prompt       use the body verbatim, no role contract
  --assignee PROFILE     Hermes profile that runs the card      (default: default)

Body
  --body-file PATH       requirement text ('-' = stdin)
  --body TEXT            requirement text (prefer --body-file)

Workspace
  --repo ABS_PATH        git repo -> --workspace worktree:<ABS_PATH>
  --workspace SPEC       scratch | worktree:<abs> | dir:<abs>  (overrides --repo)
  --branch NAME          branch for a worktree card            (default: wt/<slug>)
  --project SLUG         anchor the card under a Hermes project

Run
  --model M --provider P --reasoning L
  --skill NAME           repeatable, preloaded into the worker
  --max-runtime SEC      worker runtime cap                     (default: 1800)
  --priority N --tenant T --idempotency-key K
  --created-by NAME      attribution shown on the board         (default: auto-detect harness)
  --board SLUG           kanban board

Flow
  --no-dispatch          create only
  --max-spawn N          dispatch cap                            (default: 1)
  --wait SEC             poll until terminal status (0 = return after dispatch, default: 900)
  --poll SEC             poll interval                           (default: 5)
  --dry-run              print the create command, change nothing
  --json                 machine-readable final report

Exit: 0 done | 3 awaiting review | 4 blocked/failed | 5 wait timeout | 2 usage error`;

const ROLE_PROMPTS = {
  worker: `ROLE: worker (implementation)
Work only inside this task's workspace.
1. Read the requirement, then inspect the code before editing.
2. Make the smallest change that satisfies it; run the repo's checks and tests when available.
3. Commit on this task's branch when the workspace is a git worktree.
4. Post progress with kanban_comment.
Finish with exactly one of:
- kanban_complete(result=what changed, how it was verified, what is left)
- kanban_request_review(summary=...) when a reviewer or human must judge it
- kanban_block(reason=...) when you cannot proceed`,
  reviewer: `ROLE: reviewer
Judge the implementation; do not rewrite the feature.
1. Read the card body, the worker's summary and comments, and the diff on the task branch.
2. Check correctness, test coverage, and scope creep.
Finish with exactly one of:
- kanban_complete(result=acceptance verdict plus the evidence you checked)
- kanban_request_changes(reason=concrete changes required before re-review)
- kanban_block(reason=...) when the review cannot be performed`,
  verifier: `ROLE: verifier
Gate the work; do not extend it.
1. Read the card body and the worker's summary.
2. Run the acceptance commands yourself and capture their output.
3. Inspect the diff for regressions and scope creep.
Finish with exactly one of:
- kanban_complete(result=verdict plus the command output you relied on)
- kanban_request_changes(reason=concrete failures, with the failing output)
- kanban_block(reason=...) when verification is impossible`,
};

const TERMINAL = new Set(['done', 'blocked', 'archived']);

function fail(msg, code = 2) {
  process.stderr.write(`hermes-role-task: ${msg}\n`);
  if (code === 2) process.stderr.write('run with --help for usage\n');
  process.exit(code);
}

function resolveHermes() {
  const explicit = process.env.HERMES_BIN;
  if (explicit) return { exe: explicit, shell: false };
  const names = process.platform === 'win32'
    ? ['hermes.exe', 'hermes.cmd', 'hermes.bat', 'hermes']
    : ['hermes'];
  for (const dir of (process.env.PATH || '').split(path.delimiter).filter(Boolean)) {
    for (const name of names) {
      const candidate = path.join(dir, name);
      try {
        if (fs.existsSync(candidate)) return { exe: candidate, shell: false };
      } catch { /* unreadable PATH entry */ }
    }
  }
  return { exe: 'hermes', shell: process.platform === 'win32' };
}

const HERMES = resolveHermes();

function run(args) {
  const res = spawnSync(HERMES.exe, args, {
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
    shell: HERMES.shell,
    windowsHide: true,
  });
  if (res.error) fail(`could not run hermes (${args.join(' ')}): ${res.error.message}`);
  return { code: res.status ?? 1, out: (res.stdout || '').trim(), err: (res.stderr || '').trim() };
}

function parseJson(text) {
  if (!text) return null;
  const brace = text.indexOf('{');
  const bracket = text.indexOf('[');
  const start = brace === -1 ? bracket : bracket === -1 ? brace : Math.min(brace, bracket);
  if (start >= 0) {
    try { return JSON.parse(text.slice(start)); } catch { /* fall through to JSONL */ }
  }
  const lines = text.split(/\r?\n/).filter((l) => l.trim().startsWith('{'));
  for (let i = lines.length - 1; i >= 0; i--) {
    try { return JSON.parse(lines[i]); } catch { /* keep scanning */ }
  }
  return null;
}

function pickTask(obj) {
  if (!obj || typeof obj !== 'object') return null;
  if (typeof obj.status === 'string' && obj.id) return obj;
  for (const key of ['task', 'data', 'result']) {
    if (obj[key] && typeof obj[key] === 'object' && obj[key].id) return obj[key];
  }
  return null;
}

function parseArgs(argv) {
  const opts = { skill: [] };
  const takesValue = new Set([
    '--title', '--role', '--assignee', '--body-file', '--body', '--repo', '--workspace',
    '--branch', '--project', '--model', '--provider', '--reasoning', '--skill',
    '--max-runtime', '--priority', '--tenant', '--idempotency-key', '--created-by',
    '--board', '--max-spawn', '--wait', '--poll',
  ]);
  for (let i = 0; i < argv.length; i++) {
    const raw = argv[i];
    if (raw === '-h' || raw === '--help') { process.stdout.write(`${USAGE}\n`); process.exit(0); }
    const eq = raw.indexOf('=');
    const key = eq === -1 ? raw : raw.slice(0, eq);
    let value = eq === -1 ? undefined : raw.slice(eq + 1);
    if (!key.startsWith('--')) fail(`unknown argument ${raw}`);
    if (value === undefined) {
      if (takesValue.has(key)) {
        value = argv[++i];
        if (value === undefined) fail(`${key} needs a value`);
      } else {
        value = true;
      }
    }
    const name = key.slice(2).replace(/-/g, '_');
    if (key === '--skill') opts.skill.push(value);
    else opts[name] = value;
  }
  return opts;
}

function detectHarness() {
  const env = process.env;
  if (env.CODEX_HOME || env.CODEX_SANDBOX) return 'codex';
  if (env.CLAUDECODE || env.CLAUDE_CODE_ENTRYPOINT) return 'claude-code';
  if (env.QODER_SESSION_ID || env.QODER_HOME) return 'qoder';
  return 'harness';
}

function slug(text, max = 40) {
  const s = text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return (s || 'task').slice(0, max);
}

function readBody(opts) {
  if (opts.body_file) {
    if (opts.body_file === '-') return fs.readFileSync(0, 'utf8');
    if (!fs.existsSync(opts.body_file)) fail(`--body-file not found: ${opts.body_file}`);
    return fs.readFileSync(opts.body_file, 'utf8');
  }
  if (opts.body) return String(opts.body);
  fail('need a requirement: --body-file PATH or --body TEXT');
  return '';
}

function resolveWorkspace(opts) {
  if (opts.workspace) return { spec: String(opts.workspace), repo: null };
  if (!opts.repo) return { spec: 'scratch', repo: null };
  const repo = path.resolve(String(opts.repo));
  if (!fs.existsSync(repo)) fail(`--repo does not exist: ${repo}`);
  const git = spawnSync('git', ['-C', repo, 'rev-parse', '--show-toplevel'], { encoding: 'utf8', windowsHide: true });
  if (git.error) process.stderr.write(`hermes-role-task: cannot verify git repo (git missing): ${git.error.message}\n`);
  else if (git.status !== 0) fail(`--repo is not inside a git repository: ${repo}\n${(git.stderr || '').trim()}`);
  return { spec: `worktree:${repo}`, repo };
}

function buildBody(opts, requirement) {
  const role = (opts.role || 'worker').toLowerCase();
  if (opts.no_role_prompt === true || role === 'none') return requirement;
  const contract = ROLE_PROMPTS[role];
  if (!contract) fail(`unknown --role ${role} (worker | reviewer | verifier | none)`);
  return `${contract}\n\n--- REQUIREMENT ---\n${requirement.trim()}\n`;
}

function createArgs(opts, bodyPath, workspaceSpec, branch) {
  const args = ['kanban', 'create', String(opts.title), '--body-file', bodyPath, '--json'];
  args.push('--assignee', String(opts.assignee || 'default'));
  args.push('--workspace', workspaceSpec);
  if (workspaceSpec.startsWith('worktree')) args.push('--branch', branch);
  if (opts.project) args.push('--project', String(opts.project));
  if (opts.model) args.push('--model', String(opts.model));
  if (opts.provider) args.push('--provider', String(opts.provider));
  if (opts.reasoning) args.push('--reasoning', String(opts.reasoning));
  for (const skill of opts.skill) args.push('--skill', String(skill));
  args.push('--max-runtime', String(opts.max_runtime || 1800));
  if (opts.priority) args.push('--priority', String(opts.priority));
  if (opts.tenant) args.push('--tenant', String(opts.tenant));
  if (opts.idempotency_key) args.push('--idempotency-key', String(opts.idempotency_key));
  args.push('--created-by', String(opts.created_by || detectHarness()));
  return args;
}

function quoteForDisplay(args) {
  return args.map((a) => (/[\s"]/.test(a) ? `"${a.replace(/"/g, '\\"')}"` : a)).join(' ');
}

function report(task, extra = {}) {
  const fields = {
    id: task?.id, title: task?.title, status: task?.status,
    assignee: task?.assignee, role: extra.role,
    workspace_kind: task?.workspace_kind, workspace_path: task?.workspace_path,
    branch_name: task?.branch_name, session_id: task?.session_id,
    result: task?.result, last_failure_error: task?.last_failure_error,
    created_by: task?.created_by, gui: 'Hermes desktop app -> Kanban board',
    ...extra,
  };
  return fields;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (!opts.title) fail('--title is required');

  const version = run(['--version']);
  if (version.code !== 0) fail(`hermes CLI unavailable: ${version.err || version.out}`);

  const requirement = readBody(opts);
  const body = buildBody(opts, requirement);
  const { spec: workspaceSpec } = resolveWorkspace(opts);
  const branch = opts.branch ? String(opts.branch) : `wt/${slug(String(opts.title))}`;
  const role = (opts.role || 'worker').toLowerCase();

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hermes-role-'));
  const bodyPath = path.join(tmpDir, 'card-body.md');
  try {
    fs.writeFileSync(bodyPath, body, 'utf8');
    const args = createArgs(opts, bodyPath, workspaceSpec, branch);

    if (opts.dry_run === true) {
      process.stdout.write(`dry run: hermes ${quoteForDisplay(args)}\n\n--- card body ---\n${body}`);
      return 0;
    }

    const created = run(args);
    const task0 = pickTask(parseJson(created.out));
    if (created.code !== 0 || !task0?.id) {
      process.stderr.write(`${created.out}\n${created.err}\n`);
      fail('kanban create failed', 4);
    }
    const id = String(task0.id);
    process.stdout.write(`card ${id} "${task0.title}" role=${role} status=${task0.status} workspace=${workspaceSpec}\n`);
    process.stdout.write(`gui: open the Hermes desktop app -> Kanban board -> ${id}\n`);

    if (opts.no_dispatch !== true) {
      const dispatched = run(['kanban', 'dispatch', '--max', String(opts.max_spawn || 1), '--json']);
      const info = parseJson(dispatched.out);
      const spawned = info?.spawned ?? info?.spawned_count;
      if (dispatched.code !== 0) {
        process.stderr.write(`dispatch failed: ${dispatched.err || dispatched.out}\n`);
      } else if (spawned === 0) {
        process.stdout.write('dispatch spawned nothing (card not ready, profile busy, or emergency stop); see references/troubleshooting.md\n');
      } else {
        process.stdout.write(`dispatched: ${JSON.stringify(info?.spawned ?? info)}\n`);
      }
    }

    const waitSec = opts.wait === undefined ? 900 : Number(opts.wait);
    const pollSec = Math.max(1, Number(opts.poll || 5));
    if (!Number.isFinite(waitSec) || waitSec <= 0) return exitWith(task0, role, 'no-wait');

    const deadline = Date.now() + waitSec * 1000;
    let task = task0;
    let lastStatus = task0.status;
    while (Date.now() < deadline) {
      const shown = run(['kanban', 'show', id, '--json']);
      const current = pickTask(parseJson(shown.out));
      if (current) {
        task = current;
        if (current.status !== lastStatus) {
          process.stdout.write(`status: ${lastStatus} -> ${current.status}\n`);
          lastStatus = current.status;
        }
        if (TERMINAL.has(current.status) || current.status === 'review') break;
      }
      const nap = spawnSync(process.execPath, ['-e', `setTimeout(()=>{},${pollSec * 1000})`], { windowsHide: true });
      if (nap.error) break;
    }

    if (!TERMINAL.has(task.status) && task.status !== 'review') return exitWith(task, role, 'timeout', 5);
    return exitWith(task, role, task.status);
  } finally {
    try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch { /* temp cleanup is best effort */ }
  }
}

function exitWith(task, role, outcome, forcedCode) {
  const payload = report(task, { role, outcome });
  if (task.status === 'blocked' || task.last_failure_error) {
    const log = run(['kanban', 'log', String(task.id), '--tail', '4000']);
    const tail = (log.out || log.err || '').split(/\r?\n/).slice(-40).join('\n');
    if (tail) payload.log_tail = tail;
  }
  const asJson = process.argv.includes('--json');
  if (asJson) process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
  else {
    process.stdout.write(`\noutcome: ${outcome} (status=${task.status})\n`);
    if (task.result) process.stdout.write(`result: ${task.result}\n`);
    if (task.last_failure_error) process.stdout.write(`failure: ${task.last_failure_error}\n`);
    if (task.workspace_path) process.stdout.write(`workspace: ${task.workspace_path} (branch ${task.branch_name || '-'})\n`);
    if (task.session_id) process.stdout.write(`session: ${task.session_id}\n`);
    if (payload.log_tail) process.stdout.write(`log tail:\n${payload.log_tail}\n`);
  }
  if (forcedCode) return forcedCode;
  if (task.status === 'review') return 3;
  if (task.status === 'done') return 0;
  return 4;
}

try {
  process.exitCode = main();
} catch (err) {
  fail(err?.message || String(err));
}
