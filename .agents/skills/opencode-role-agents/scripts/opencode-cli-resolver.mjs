import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

function isFile(file) {
  try { return fs.statSync(file).isFile(); } catch { return false; }
}

export function resolveOpencode({ env = process.env, platform = process.platform } = {}) {
  const explicit = env.OPENCODE_CLI_BIN;
  if (explicit) {
    if (/\.(cmd|bat|ps1)$/i.test(explicit)) {
      throw new Error(`OPENCODE_CLI_BIN points at a shell shim (${explicit}); point it at a native OpenCode executable`);
    }
    if (!isFile(explicit)) throw new Error(`OPENCODE_CLI_BIN not found: ${explicit}`);
    return { exe: explicit, label: explicit };
  }

  const delimiter = platform === 'win32' ? ';' : path.delimiter;
  const dirs = (env.PATH || '').split(delimiter).filter(Boolean);
  if (platform === 'win32') {
    for (const dir of dirs) {
      const candidate = path.join(dir, 'opencode.exe');
      if (isFile(candidate)) return { exe: candidate, label: candidate };
    }
    // npm's Windows bin entries are .cmd/.ps1/extensionless shims. Spawn the
    // package's native binary directly instead of asking CreateProcess to run one.
    for (const dir of dirs) {
      const candidate = path.join(dir, 'node_modules', '@opencode', 'cli', 'bin', 'opencode.exe');
      if (isFile(candidate)) return { exe: candidate, label: candidate };
    }
    const local = env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
    const bundled = path.join(local, 'Programs', 'ai.opencode.desktop', 'resources', 'opencode-cli.exe');
    if (isFile(bundled)) return { exe: bundled, label: bundled };
  } else {
    for (const dir of dirs) {
      const candidate = path.join(dir, 'opencode');
      if (isFile(candidate)) return { exe: candidate, label: candidate };
    }
    if (platform === 'darwin') {
      for (const candidate of [
        '/Applications/OpenCode.app/Contents/Resources/opencode-cli',
        '/Applications/OpenCode.app/Contents/MacOS/OpenCode',
      ]) {
        if (isFile(candidate)) return { exe: candidate, label: candidate };
      }
    }
  }

  throw new Error('could not find the OpenCode CLI. Install OpenCode, put its native executable on PATH, or point OPENCODE_CLI_BIN at it');
}
