import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { resolveOpencode } from './opencode-cli-resolver.mjs';

test('resolves npm global install to its native Windows executable', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'opencode-cli-resolver-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const npmPrefix = path.join(root, 'npm');
  const native = path.join(npmPrefix, 'node_modules', '@opencode', 'cli', 'bin', 'opencode.exe');
  fs.mkdirSync(path.dirname(native), { recursive: true });
  fs.writeFileSync(path.join(npmPrefix, 'opencode'), 'npm shim');
  fs.writeFileSync(native, 'native executable placeholder');

  const result = resolveOpencode({
    env: { PATH: npmPrefix, LOCALAPPDATA: path.join(root, 'local') },
    platform: 'win32',
  });

  assert.equal(result.exe, native);
});

test('does not select an extensionless npm shim on Windows', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'opencode-cli-shim-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const npmPrefix = path.join(root, 'npm');
  fs.mkdirSync(npmPrefix, { recursive: true });
  fs.writeFileSync(path.join(npmPrefix, 'opencode'), 'npm shim');

  assert.throws(
    () => resolveOpencode({
      env: { PATH: npmPrefix, LOCALAPPDATA: path.join(root, 'local') },
      platform: 'win32',
    }),
    /could not find the OpenCode CLI/,
  );
});

test('rejects Windows shell shims supplied as OPENCODE_CLI_BIN', () => {
  assert.throws(
    () => resolveOpencode({ env: { OPENCODE_CLI_BIN: 'C:\\tools\\opencode.cmd' }, platform: 'win32' }),
    /shell shim/,
  );
});
