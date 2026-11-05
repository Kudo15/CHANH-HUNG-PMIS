import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const script = path.join(path.dirname(fileURLToPath(import.meta.url)), 'opencode-role-task.mjs');

test('dry-run prints the task without creating ledger or run files', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'opencode-role-dry-run-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const ledger = path.join(root, 'ledger');
  const result = spawnSync(process.execPath, [
    script,
    '--title', 'dry-run regression',
    '--role', 'worker',
    '--body', 'Return only the synthetic answer.',
    '--ledger', ledger,
    '--dry-run',
  ], { cwd: process.cwd(), encoding: 'utf8', windowsHide: true });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /dry run:/);
  assert.equal(fs.existsSync(ledger), false);
});

test('malformed timeout exits as usage error before creating ledger files', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'opencode-role-timeout-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const ledger = path.join(root, 'ledger');
  const result = spawnSync(process.execPath, [
    script,
    '--title', 'invalid timeout regression',
    '--role', 'worker',
    '--body', 'probe',
    '--ledger', ledger,
    '--timeout', 'invalid',
  ], { cwd: process.cwd(), encoding: 'utf8', windowsHide: true });

  assert.equal(result.status, 2, result.stderr);
  assert.match(result.stderr, /--timeout must be a positive finite number/);
  assert.equal(fs.existsSync(ledger), false);
});
