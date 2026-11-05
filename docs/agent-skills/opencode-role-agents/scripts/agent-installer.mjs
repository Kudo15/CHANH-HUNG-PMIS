import fs from 'node:fs';
import path from 'node:path';

const ROLE_FILES = ['worker', 'reviewer', 'verifier'];

export function installRoleAgents({ sourceDir, destDir, force = false, version = 4, roles = ROLE_FILES }) {
  const plan = [];
  const blocked = [];

  for (const role of roles) {
    const src = path.join(sourceDir, `role-${role}.md`);
    if (!fs.existsSync(src)) throw new Error(`skill is incomplete: missing ${src}`);
    const content = fs.readFileSync(src, 'utf8');
    const dest = path.join(destDir, `role-${role}.md`);
    if (!fs.existsSync(dest)) {
      plan.push({ dest, content, action: 'write' });
      continue;
    }

    const current = fs.readFileSync(dest, 'utf8');
    if (current === content) continue;
    if (force) {
      plan.push({ dest, content, action: 'write' });
      continue;
    }

    const marker = current.match(/<!--\s*opencode-role-agents:(\d+)\s*-->/);
    if (!marker) {
      blocked.push(dest);
      continue;
    }
    const currentVersion = Number(marker[1]);
    if (currentVersion < version) {
      plan.push({ dest, content, action: 'write' });
    } else if (currentVersion > version || !current.includes('ROLE_RESULT:')) {
      blocked.push(dest);
    }
    // A current-version file with the role-result contract may be user-edited;
    // preserve it unless --force-agents explicitly opts into replacement.
  }

  if (blocked.length) return { dir: destDir, installed: [], blocked };

  const installed = [];
  for (const item of plan) {
    fs.mkdirSync(path.dirname(item.dest), { recursive: true });
    fs.writeFileSync(item.dest, item.content, 'utf8');
    installed.push(item.dest);
  }
  return { dir: destDir, installed, blocked: [] };
}
