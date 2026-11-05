import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { installRoleAgents } from './agent-installer.mjs';

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'opencode-agent-install-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const sourceDir = path.join(root, 'source');
  const destDir = path.join(root, 'config', 'agents');
  fs.mkdirSync(sourceDir, { recursive: true });
  for (const role of ['worker', 'reviewer', 'verifier']) {
    fs.writeFileSync(path.join(sourceDir, `role-${role}.md`),
      `---\ndescription: ${role}\n---\n<!-- opencode-role-agents:4 -->\nROLE_RESULT: done\n`);
  }
  return { sourceDir, destDir };
}

test('preserves and blocks on an unmarked user agent without partial installs', (t) => {
  const { sourceDir, destDir } = fixture(t);
  fs.mkdirSync(destDir, { recursive: true });
  const custom = path.join(destDir, 'role-worker.md');
  fs.writeFileSync(custom, 'user-owned custom worker prompt');

  const result = installRoleAgents({ sourceDir, destDir });

  assert.deepEqual(result.installed, []);
  assert.deepEqual(result.blocked, [custom]);
  assert.equal(fs.readFileSync(custom, 'utf8'), 'user-owned custom worker prompt');
  assert.equal(fs.existsSync(path.join(destDir, 'role-reviewer.md')), false);
});

test('upgrades only an older skill-marked agent and installs missing roles', (t) => {
  const { sourceDir, destDir } = fixture(t);
  fs.mkdirSync(destDir, { recursive: true });
  const worker = path.join(destDir, 'role-worker.md');
  fs.writeFileSync(worker, '<!-- opencode-role-agents:3 -->\nold prompt');

  const result = installRoleAgents({ sourceDir, destDir });

  assert.deepEqual(result.blocked, []);
  assert.deepEqual(result.installed.sort(), [
    path.join(destDir, 'role-reviewer.md'),
    path.join(destDir, 'role-verifier.md'),
    worker,
  ].sort());
  assert.match(fs.readFileSync(worker, 'utf8'), /opencode-role-agents:4/);
});

test('preserves a current skill-owned prompt that a user edited', (t) => {
  const { sourceDir, destDir } = fixture(t);
  fs.mkdirSync(destDir, { recursive: true });
  const worker = path.join(destDir, 'role-worker.md');
  const custom = '<!-- opencode-role-agents:4 -->\nROLE_RESULT: done\ncustomized';
  fs.writeFileSync(worker, custom);

  const result = installRoleAgents({ sourceDir, destDir });

  assert.deepEqual(result.blocked, []);
  assert.equal(fs.readFileSync(worker, 'utf8'), custom);
});

test('requires explicit force to replace a user-owned or newer agent', (t) => {
  const { sourceDir, destDir } = fixture(t);
  fs.mkdirSync(destDir, { recursive: true });
  const worker = path.join(destDir, 'role-worker.md');
  fs.writeFileSync(worker, '<!-- opencode-role-agents:5 -->\nfuture prompt');

  const blocked = installRoleAgents({ sourceDir, destDir });
  assert.deepEqual(blocked.installed, []);
  assert.deepEqual(blocked.blocked, [worker]);
  assert.match(fs.readFileSync(worker, 'utf8'), /future prompt/);

  const forced = installRoleAgents({ sourceDir, destDir, force: true });
  assert.deepEqual(forced.blocked, []);
  assert.match(fs.readFileSync(worker, 'utf8'), /opencode-role-agents:4/);
});
