#!/usr/bin/env node
// Runs one OpenCode role agent headlessly through the shared desktop service and records it.
import { spawnSync } from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { installRoleAgents } from './agent-installer.mjs';
import { resolveOpencode } from './opencode-cli-resolver.mjs';
import { timeoutMilliseconds } from './role-task-options.mjs';

const SKILL_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

const USAGE = `opencode-role-task.mjs - run one OpenCode role agent and record it in a ledger

Usage:
  node opencode-role-task.mjs --title "..." (--body TEXT | --body-file PATH) [options]
  node opencode-role-task.mjs --list [--limit N]
  node opencode-role-task.mjs --status [--json]

Task:
  --title TEXT            Short task title; stored as "<role>: <title>" in the GUI
  --body TEXT             Requirement text (single line)
  --body-file PATH        Requirement text from a file; use this for multi-line bodies

Role:
  --role NAME             worker (default) | reviewer | verifier
  --agent NAME            Override the OpenCode agent name (default role-<role>)
  --model NAME            Passed to opencode run --model (provider/model)
  --no-auto               Do not pass --auto; the run keeps OpenCode's ask-level permissions
  --force-agents          Replace conflicting role agent files under ~/.config/opencode/agents
  --no-install-agents     Skip installing the role agent files
  --extra ARG             Extra raw opencode argument, repeatable

Workspace:
  --repo PATH             Git repository the role works in (resolved to its root)
  --cwd PATH              Working directory when --repo is omitted (default: current dir)

Run control:
  --timeout SECONDS       Kill the run after N seconds (positive; min 30; default 1800)
  --resume ID             Continue an existing session id instead of creating one
  --ledger DIR            Ledger root (default ~/.opencode/role-runs, env OPENCODE_ROLE_LEDGER)
  --dry-run               Print the exact command and body, run nothing
  --json                  Print the full ledger record as JSON
  --list                  Print the ledger board and exit
  --status                Check the CLI, service URL, desktop app and API health, then exit
  --help                  Show this help

Exit codes: 0 done, 1 run failed, 2 usage, 3 review requested, 4 blocked,
            5 timeout, 6 CLI unusable, 7 not signed in / no model available
`;

const ROLE_AGENT = { worker: 'role-worker', reviewer: 'role-reviewer', verifier: 'role-verifier' };
const MAX_BODY_CHARS = 30000;
let OPENCODE;

const TAKES_VALUE = new Set([
  '--title', '--body', '--body-file', '--role', '--agent', '--model', '--extra',
  '--repo', '--cwd', '--timeout', '--resume', '--ledger', '--limit'
]);

function fail(msg, code = 2) {
  process.stderr.write(`opencode-role-task: ${msg}\n`);
  if (code === 2) process.stderr.write('run with --help for usage\n');
  process.exit(code);
}

function parseArgs(argv) {
  const opts = { role: 'worker', extra: [] };
  for (let i = 0; i < argv.length; i++) {
    let arg = argv[i];
    let inline = null;
    const eq = arg.indexOf('=');
    if (arg.startsWith('--') && eq > 0) { inline = arg.slice(eq + 1); arg = arg.slice(0, eq); }
    const key = arg.replace(/^--/, '').replace(/-/g, '_');
    const value = () => {
      if (inline !== null) return inline;
      const next = argv[++i];
      if (next === undefined) fail(`missing value for ${arg}`);
      return next;
    };
    if (!arg.startsWith('--')) fail(`unexpected positional argument: ${arg}`);
    if (TAKES_VALUE.has(arg)) {
      const v = value();
      if (arg === '--extra') opts.extra.push(v);
      else opts[key] = v;
      continue;
    }
    const flags = {
      '--no-auto': 'no_auto', '--force-agents': 'force_agents',
      '--no-install-agents': 'no_install_agents', '--dry-run': 'dry_run',
      '--json': 'json', '--list': 'list', '--help': 'help', '--status': 'status'
    };
    if (flags[arg]) { opts[flags[arg]] = true; continue; }
    fail(`unknown argument: ${arg}`);
  }
  return opts;
}

function detectHarness() {
  const e = process.env;
  if (e.CODEX_HOME || e.CODEX_SANDBOX) return 'codex';
  if (e.CLAUDECODE || e.CLAUDE_CODE_ENTRYPOINT) return 'claude-code';
  if (e.QODER_SESSION_ID || e.QODER_HOME) return 'qoder';
  return 'harness';
}

function run(args, opts = {}) {
  const res = spawnSync(OPENCODE.exe, args, {
    encoding: 'utf8', maxBuffer: 128 * 1024 * 1024, windowsHide: true,
    cwd: opts.cwd, timeout: opts.timeout, input: opts.input,
    // The CLI resolves the session project from PWD, which a parent shell exports;
    // without this the session lands in the caller's directory instead of --repo/--cwd.
    env: { ...process.env, PWD: opts.cwd || process.cwd() }
  });
  if (res.error && !opts.allowError) {
    fail(`could not run opencode (${args[0] ?? ''}): ${res.error.message}`, 6);
  }
  return {
    code: res.status ?? 1,
    out: res.stdout || '',
    err: res.stderr || '',
    signal: res.signal,
    error: res.error
  };
}

function git(args, cwd) {
  const res = spawnSync('git', args, { encoding: 'utf8', cwd, windowsHide: true, maxBuffer: 8 * 1024 * 1024 });
  return { code: res.status ?? 1, out: (res.stdout || '').trim(), err: (res.stderr || '').trim() };
}

function ledgerRoot(opts, create = true) {
  const given = opts.ledger || process.env.OPENCODE_ROLE_LEDGER;
  const dir = given
    ? path.resolve(String(given))
    : path.join(os.homedir(), '.opencode', 'role-runs');
  if (given && !path.isAbsolute(String(given))) {
    process.stderr.write(`opencode-role-task: note: relative ledger resolved to ${dir}\n`);
    process.stderr.write('opencode-role-task: a ledger inside a disposable task workspace is lost when that workspace is cleaned up\n');
  }
  if (create) fs.mkdirSync(path.join(dir, 'runs'), { recursive: true });
  return dir;
}

function slug(text) {
  return String(text).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'task';
}

function appendBoard(root, record) {
  fs.appendFileSync(path.join(root, 'board.jsonl'), `${JSON.stringify(record)}\n`, 'utf8');
}

function parseRoleResult(text) {
  const lines = String(text).split(/\r?\n/).map((l) => l.trim());
  let result = null; let summary = null;
  for (const line of lines) {
    const r = line.match(/^ROLE_RESULT:\s*(done|review|blocked)\s*$/i);
    if (r) result = r[1].toLowerCase();
    const s = line.match(/^SUMMARY:\s*(.+)$/i);
    if (s) summary = s[1].trim();
  }
  return { result, summary };
}

function parseEvents(text) {
  let sessionId = null;
  const texts = [];
  const errors = [];
  for (const line of String(text).split(/\r?\n/)) {
    const raw = line.trim();
    if (!raw.startsWith('{')) continue;
    let ev;
    try { ev = JSON.parse(raw); } catch { continue; }
    if (ev.sessionID && !sessionId) sessionId = ev.sessionID;
    if (ev.type === 'error') {
      errors.push(ev.error?.message || ev.error?.type || JSON.stringify(ev.error || ev).slice(0, 300));
    }
    if (ev.part && ev.part.type === 'text' && typeof ev.part.text === 'string') texts.push(ev.part.text);
  }
  return { sessionId, transcript: texts.join('\n\n').trim(), errors };
}

function agentsDir() {
  return process.env.OPENCODE_AGENTS_DIR
    ? path.resolve(process.env.OPENCODE_AGENTS_DIR)
    : path.join(os.homedir(), '.config', 'opencode', 'agents');
}

function ensureAgents(opts) {
  return installRoleAgents({
    sourceDir: path.join(SKILL_DIR, 'agents'),
    destDir: agentsDir(),
    force: opts.force_agents,
  });
}

function serviceStateFile() {
  return path.join(os.homedir(), '.local', 'state', 'opencode', 'service.json');
}

function readServiceState() {
  try { return JSON.parse(fs.readFileSync(serviceStateFile(), 'utf8')); } catch { return null; }
}

function pidAlive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try { process.kill(pid, 0); return true; } catch (err) { return err.code === 'EPERM'; }
}

function desktopRunning() {
  if (process.platform === 'win32') {
    const res = spawnSync('tasklist', ['/FI', 'IMAGENAME eq OpenCode.exe', '/NH'],
      { encoding: 'utf8', windowsHide: true, timeout: 30000 });
    if (res.error || res.status === null) return null;
    if (res.status !== 0) return null;
    return /OpenCode\.exe/i.test(res.stdout || '');
  }
  const res = spawnSync('pgrep', ['-f', 'OpenCode'], { encoding: 'utf8', timeout: 15000 });
  if (res.error || res.status === null) return null;
  return res.status === 0;
}

async function probeService(url, password) {
  if (!password) return { status: null, note: 'no password in the service state file' };
  const auth = Buffer.from(`opencode:${password}`).toString('base64');
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 5000);
  try {
    const res = await fetch(`${url.replace(/\/$/, '')}/api/info`,
      { headers: { Authorization: `Basic ${auth}` }, signal: ctl.signal });
    return { status: res.status, ok: res.ok };
  } catch (err) {
    return { status: null, note: err.name === 'AbortError' ? 'timed out' : err.message };
  } finally {
    clearTimeout(timer);
  }
}

// One command that answers "is this machine able to run a GUI-visible role task?" without
// relying on a PATH shim: the bundled CLI is not on PATH.
async function printStatus(opts) {
  const info = {
    cli: OPENCODE.exe,
    version: null,
    service_url: null,
    service_pid: null,
    service_pid_alive: null,
    service_state_file: serviceStateFile(),
    desktop_running: null,
    api: null
  };
  const version = run(['--version'], { allowError: true, timeout: 60000 });
  info.version = (version.out || version.err).trim().split(/\r?\n/)[0] || null;
  if (version.error) info.cli_error = version.error.message;
  const status = run(['service', 'status'], { allowError: true, timeout: 60000 });
  if (status.error && !info.cli_error) info.cli_error = status.error.message;
  const url = ((status.out || '') + '\n' + (status.err || '')).match(/https?:\/\/[^\s"']+/);
  info.service_url = url ? url[0] : null;
  const state = readServiceState();
  if (state) {
    info.service_pid = state.pid ?? null;
    info.service_pid_alive = pidAlive(state.pid);
  }
  info.desktop_running = desktopRunning();
  if (info.service_url) info.api = await probeService(info.service_url, state?.password);

  if (opts.json) {
    process.stdout.write(`${JSON.stringify(info, null, 2)}\n`);
    return info.service_url && info.api?.ok ? 0 : 6;
  }
  process.stdout.write(
    `cli: ${info.cli}\n` +
    `version: ${info.version || '-'}\n` +
    `service: ${info.service_url || 'not running'}` +
    `${info.service_pid ? `  (state pid ${info.service_pid}, ${info.service_pid_alive ? 'alive' : 'dead'})` : ''}\n` +
    `desktop app: ${info.desktop_running === null ? 'unknown (process listing unavailable)' : info.desktop_running ? 'running' : 'not running'}\n` +
    `api: ${info.api ? (info.api.ok ? `ok (${info.api.status})` : `unhealthy (${info.api.status ?? info.api.note})`) : '-'}\n`);
  if (!info.service_url) {
    if (!info.version) {
      process.stderr.write(
        'opencode-role-task: the CLI produced no output' +
        `${info.cli_error ? ` (${info.cli_error})` : ''}. If you are inside a sandbox, rerun with ` +
        'the access this command needs: it executes the resolved native OpenCode CLI, reads ' +
        '~/.local/share/opencode/log and ~/.local/state/opencode/service.json, calls tasklist ' +
        'and connects to 127.0.0.1. These checks are free.\n');
      return 6;
    }
    process.stderr.write('opencode-role-task: no service URL; run the driver once to let it start ' +
      'the service (it resolves the CLI itself), or see references/troubleshooting.md\n');
    return 6;
  }
  return info.api?.ok ? 0 : 6;
}

function preflight(record) {
  const version = run(['--version'], { allowError: true, timeout: 60000 });
  record.cli_version = (version.out || version.err).trim().split(/\r?\n/)[0] || null;
  if (version.code !== 0 && !record.cli_version) {
    const detail = version.error ? ` (${version.error.message})` : '';
    record.preflight_error = `could not run ${OPENCODE.exe}${detail}. In a sandbox this check may be ` +
      'blocked; rerun with access to the resolved CLI, ~/.local/share/opencode/log, ' +
      '~/.local/state/opencode/service.json, tasklist and 127.0.0.1';
    return false;
  }
  let status = run(['service', 'status'], { allowError: true, timeout: 60000 });
  if (status.code !== 0) {
    process.stderr.write('opencode-role-task: background service is not running; starting it ' +
      'so the run is visible in the OpenCode Desktop GUI\n');
    run(['service', 'start'], { allowError: true, timeout: 120000 });
    status = run(['service', 'status'], { allowError: true, timeout: 60000 });
  }
  const url = ((status.out || '') + '\n' + (status.err || '')).match(/https?:\/\/[^\s"']+/);
  record.service_url = url ? url[0] : null;
  if (!record.service_url) {
    // A half-booted service keeps the port while the CLI reports "stopped"; starting again fails
    // and the run dies later with an opaque message. Name the process to stop instead.
    const state = readServiceState();
    if (state && pidAlive(state.pid)) {
      const kill = process.platform === 'win32' ? `taskkill /PID ${state.pid} /F` : `kill ${state.pid}`;
      record.service_state = { pid: state.pid, url: state.url || null, alive: true };
      record.preflight_error = `the OpenCode background service is wedged: state ${serviceStateFile()} ` +
        `still names pid ${state.pid}${state.url ? ` (${state.url})` : ''}, but the CLI reports it stopped. ` +
        `Stop that process with "${kill}", then rerun; the driver starts a fresh service.`;
      return false;
    }
    record.preflight_error = `could not resolve the background service URL (service status exit ` +
      `${status.code}${status.error ? `, ${status.error.message}` : ''}). In a sandbox this check may be ` +
      'blocked; rerun with access to the resolved CLI, ~/.local/share/opencode/log, ' +
      '~/.local/state/opencode/service.json, tasklist and 127.0.0.1. Otherwise see ' +
      'references/troubleshooting.md';
    return false;
  }
  return true;
}

function buildArgs(opts, body) {
  const role = opts.role;
  const agent = opts.agent || ROLE_AGENT[role];
  const args = ['run', '--format', 'json', '--agent', String(agent), '--title', `${role}: ${opts.title}`];
  if (opts.model) args.push('--model', String(opts.model));
  if (!opts.no_auto) args.push('--auto');
  if (opts.resume) args.push('--session', String(opts.resume));
  for (const extra of opts.extra) {
    const eq = extra.indexOf('=');
    if (eq > 0) args.push(extra.slice(0, eq), extra.slice(eq + 1));
    else args.push(extra);
  }
  // This build treats `--` as a positional and duplicates the prompt, so pass the message
  // directly. A leading dash is neutralised by the caller before we get here.
  args.push(body);
  return { args, agent };
}

function enrichFromExport(sessionId, cwd, record) {
  if (!sessionId) return null;
  const res = run(['session', 'export', sessionId], { cwd, allowError: true, timeout: 120000 });
  if (res.code !== 0) return null;
  try {
    const payload = JSON.parse(res.out);
    const info = payload.info || {};
    record.model_used = info.model
      ? `${info.model.providerID || '?'}/${info.model.id || '?'}${info.model.variant && info.model.variant !== 'default' ? `#${info.model.variant}` : ''}`
      : null;
    record.cost_usd = typeof info.cost === 'number' ? info.cost : null;
    record.tokens = info.tokens || null;
    record.session_title = info.title || null;
    record.outcome = info.outcome || null;
    record.agent_used = info.agent || null;
    record.session_directory = info.location?.directory || null;
    return payload;
  } catch { return null; }
}

function sessionListed(sessionId, cwd) {
  if (!sessionId) return false;
  const res = run(['session', 'list'], { cwd, allowError: true, timeout: 60000 });
  if (res.code !== 0) return false;
  return res.out.split(/\r?\n/).some((line) => line.trim().startsWith(`${sessionId}\t`) || line.trim() === sessionId);
}

function printBoard(opts) {
  const root = ledgerRoot(opts, false);
  const file = path.join(root, 'board.jsonl');
  if (!fs.existsSync(file)) { process.stdout.write(`no runs yet (ledger: ${root})\n`); return; }
  const limit = Number(opts.limit || 25);
  const rows = fs.readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean)
    .map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  const latest = new Map();
  for (const r of rows) latest.set(r.run_id, r);
  const list = [...latest.values()].slice(-limit).reverse();
  process.stdout.write(`ledger: ${root}\n\n`);
  for (const r of list) {
    process.stdout.write(
      `${r.ts}  ${String(r.status).padEnd(8)} ${String(r.role).padEnd(9)} ${r.run_id}\n` +
      `    ${r.title}\n` +
      `    project: ${r.cwd}\n` +
      `    session: ${r.session_id || '-'}  gui: ${r.gui_visible ? 'listed' : 'unknown'}  summary: ${r.summary || '-'}\n`);
  }
}

function failRun(root, record, status, error, code) {
  record.status = status;
  record.error = error;
  record.ended_at = new Date().toISOString();
  appendBoard(root, record);
  try { fs.writeFileSync(path.join(record.run_dir, 'meta.json'), JSON.stringify(record, null, 2), 'utf8'); } catch {}
  process.stderr.write(`opencode-role-task: ${error}\n`);
  process.exit(code);
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) { process.stdout.write(USAGE); return 0; }
  if (opts.list) { printBoard(opts); return 0; }
  try { OPENCODE = resolveOpencode(); }
  catch (err) { fail(err.message, 6); }
  if (opts.status) return printStatus(opts);

  if (!opts.title) fail('--title is required');
  const role = String(opts.role).toLowerCase();
  if (!ROLE_AGENT[role]) fail(`--role must be worker, reviewer or verifier (got ${opts.role})`);
  opts.role = role;
  let timeoutMs;
  try { timeoutMs = timeoutMilliseconds(opts.timeout); }
  catch (err) { fail(err.message); }

  let body = opts.body;
  if (opts.body_file) {
    if (!fs.existsSync(opts.body_file)) fail(`--body-file not found: ${opts.body_file}`, 1);
    body = fs.readFileSync(opts.body_file, 'utf8');
  }
  if (!body || !String(body).trim()) fail('a task body is required (--body or --body-file)');
  body = String(body).trim();
  if (body.startsWith('-')) body = `Task:\n${body}`;
  body = `${body}\n\nReport status with the SUMMARY and ROLE_RESULT lines described in your instructions.`;
  if (body.length > MAX_BODY_CHARS) {
    fail(`body is ${body.length} chars; the Windows command line limit is about 32767. ` +
      'Split the task or trim the body file.', 2);
  }

  let cwd = path.resolve(String(opts.cwd || process.cwd()));
  let repo = null;
  if (opts.repo) {
    repo = path.resolve(String(opts.repo));
    const root = git(['-C', repo, 'rev-parse', '--show-toplevel'], repo);
    if (root.code !== 0) fail(`--repo is not a git repository: ${repo}`, 2);
    repo = root.out;
    cwd = repo;
  }
  if (!fs.existsSync(cwd)) fail(`working directory not found: ${cwd}`, 2);

  const root = ledgerRoot(opts, !opts.dry_run);
  const startedAt = new Date();
  const stamp = startedAt.toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const runId = `${stamp}-${role}-${slug(opts.title)}-${crypto.randomBytes(2).toString('hex')}`;
  const runDir = path.join(root, 'runs', runId);

  const { args, agent } = buildArgs(opts, body);

  const record = {
    run_id: runId, ts: startedAt.toISOString(), title: String(opts.title), role,
    status: 'created', harness: detectHarness(), cli: OPENCODE.label,
    cwd, repo, session_id: opts.resume ? String(opts.resume) : null,
    agent, model_requested: opts.model || null, permission_mode: opts.no_auto ? 'default' : 'auto',
    auto: !opts.no_auto, run_dir: runDir, ledger: root, started_at: startedAt.toISOString(),
    gui_app: 'OpenCode Desktop'
  };

  if (opts.dry_run) {
    process.stdout.write(`dry run: ${[OPENCODE.exe, ...args]
      .map((a) => (/[\s"'\\]/.test(a) ? JSON.stringify(a) : a)).join(' ')}\n\n--- body ---\n${body}\n`);
    process.stdout.write(`\nledger: ${root}\nrun id: ${runId}\n`);
    return 0;
  }

  fs.mkdirSync(runDir, { recursive: true });
  fs.writeFileSync(path.join(runDir, 'prompt.md'), body, 'utf8');

  let agentInfo = { dir: agentsDir(), installed: [] };
  if (!opts.no_install_agents) {
    try { agentInfo = ensureAgents(opts); } catch (err) { fail(`could not install role agents: ${err.message}`, 1); }
  }
  if (agentInfo.blocked?.length) {
    fail('existing role agent file(s) are unmarked, newer than this skill, or missing ROLE_RESULT; ' +
      `they were preserved. Inspect them and rerun with --force-agents only if replacement is intended:\n  ${agentInfo.blocked.join('\n  ')}`, 1);
  }
  record.agents_dir = agentInfo.dir;
  record.agents_installed = agentInfo.installed;

  appendBoard(root, record);
  if (!preflight(record)) {
    failRun(root, record, 'failed', record.preflight_error || 'the OpenCode CLI could not be started', 6);
  }

  const res = run(args, { cwd, timeout: timeoutMs, allowError: true });
  const endedAt = new Date();

  fs.writeFileSync(path.join(runDir, 'stdout.log'), res.out || '', 'utf8');
  fs.writeFileSync(path.join(runDir, 'stderr.log'), res.err || '', 'utf8');

  const parsed = parseEvents(res.out);
  const { result: roleResult, summary } = parseRoleResult(parsed.transcript);
  const sessionId = parsed.sessionId || record.session_id;
  record.session_id = sessionId;

  enrichFromExport(sessionId, cwd, record);
  record.session_directory_matches = record.session_directory
    ? path.resolve(record.session_directory).toLowerCase() === path.resolve(cwd).toLowerCase()
    : null;
  record.gui_visible = sessionListed(sessionId, cwd) && record.session_directory_matches !== false;
  record.gui_hint = sessionId
    ? `OpenCode Desktop -> project ${cwd} -> session ${record.session_title || sessionId}`
    : null;

  record.ended_at = endedAt.toISOString();
  record.duration_ms = endedAt - startedAt;
  record.exit_code = res.code;
  record.signal = res.signal || null;
  record.summary = summary || (parsed.transcript ? parsed.transcript.split(/\r?\n/)[0].slice(0, 200) : null);
  record.role_result = roleResult || null;
  record.error_events = parsed.errors;
  record.stderr_tail = res.err ? res.err.split(/\r?\n/).slice(-10).join('\n') : null;

  let exitCode = 0;
  if (res.error && (res.error.code === 'ETIMEDOUT' || res.signal)) {
    record.status = 'timeout';
    record.error = `run exceeded ${Math.round(timeoutMs / 1000)}s`;
    exitCode = 5;
    process.stderr.write(`opencode-role-task: ${record.error}\n`);
  } else if (res.error) {
    record.status = 'failed';
    record.error = `could not run opencode: ${res.error.message}`;
    exitCode = 1;
    process.stderr.write(`opencode-role-task: ${record.error}\n`);
  } else if (parsed.errors.length) {
    record.status = 'failed';
    record.error = `opencode reported: ${parsed.errors[0]}`;
    exitCode = 1;
    process.stderr.write(`opencode-role-task: ${record.error}\n`);
  } else if (res.code !== 0) {
    record.status = 'failed';
    record.error = `opencode exited ${res.code}`;
    exitCode = 1;
    process.stderr.write(`opencode-role-task: opencode exited ${res.code}\n${record.stderr_tail || ''}\n` +
      `  transcript: ${path.join(runDir, 'stdout.log')}\n`);
  } else {
    record.status = roleResult || 'done';
    exitCode = record.status === 'review' ? 3 : record.status === 'blocked' ? 4 : 0;
  }

  fs.writeFileSync(path.join(runDir, 'meta.json'),
    JSON.stringify({ ...record, transcript_tail: parsed.transcript.slice(-4000) }, null, 2), 'utf8');
  appendBoard(root, record);

  if (exitCode === 0 || exitCode === 3 || exitCode === 4) {
    if (opts.json) process.stdout.write(`${JSON.stringify(record, null, 2)}\n`);
    else {
      const tok = record.tokens
        ? `in ${record.tokens.input ?? '-'} out ${record.tokens.output ?? '-'} cache-read ${record.tokens.cache?.read ?? '-'}`
        : '-';
      process.stdout.write(
        `run ${runId}  role=${role}  status=${record.status}\n` +
        `title: ${record.title}\n` +
        `project: ${cwd}${record.service_url ? `  (service ${record.service_url})` : ''}\n` +
        `session: ${sessionId || '-'}  gui: ${record.gui_visible ? 'listed in OpenCode Desktop' : 'not confirmed'}\n` +
        `resume: opencode run --session ${sessionId || '<id>'} "continue"\n` +
        `summary: ${record.summary || '(none reported)'}\n` +
        `model: ${record.model_used || record.model_requested || '-'}  cost: ${record.cost_usd ?? '-'}  tokens: ${tok}\n` +
        `ledger: ${path.join(root, 'board.jsonl')}  |  run dir: ${runDir}\n`);
      if (parsed.transcript) process.stdout.write(`\n--- output tail ---\n${parsed.transcript.slice(-2000)}\n`);
    }
    if (exitCode === 4) process.stderr.write(`\n--- stderr tail ---\n${record.stderr_tail || '(empty)'}\n`);
  }
  return exitCode;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  let code = 0;
  try { code = await main(); } catch (err) {
    process.stderr.write(`opencode-role-task: ${err && err.message ? err.message : err}\n`);
    code = 1;
  }
  process.exit(code);
}
