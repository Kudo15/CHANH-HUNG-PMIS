// CHPMIS-009: read-only checkpoint inventory. Never prints matched secret values.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, lstatSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = '.team/baselines/CHPMIS-009-candidates.json';
const hash = value => createHash('sha256').update(value).digest('hex');
const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
const findings = [];
const addFinding = (path, rule) => findings.push({ path, rule });

try {
  const args = process.argv.slice(2);
  if (args.length && !(args.length === 2 && args[0] === '--check')) {
    throw new Error('Usage: node scripts/audit-baseline.mjs [--check MANIFEST]');
  }
  const candidates = [...new Set(git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0').filter(Boolean))].sort();
  const untracked = new Set(git('ls-files', '--others', '--exclude-standard', '-z').split('\0').filter(Boolean));
  const entries = [];
  const secretRules = [
    ['private-key-block', /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/],
    ['github-token', /\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b/],
    ['aws-access-key', /\bAKIA[A-Z0-9]{16}\b/],
    ['jwt-value', /\beyJ[A-Za-z0-9_-]{25,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b/],
  ];
  for (const path of candidates) {
    if (path === manifestPath) continue; // The report cannot hash its own bytes.
    const absolute = resolve(root, path);
    const stat = lstatSync(absolute);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      addFinding(path, 'non-regular-candidate');
      continue;
    }
    const segments = path.split('/');
    if (segments.some(segment => /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(segment))) addFinding(path, 'windows-reserved-name');
    if (segments.some(segment => /^(node_modules|\.venv|__pycache__|dist|\.pytest_cache|\.ruff_cache|playwright-report|test-results|pgdata)$/.test(segment))) addFinding(path, 'generated-candidate');
    if ((segments.some(segment => /^\.env(?:\.|$)/.test(segment)) && path !== '.env.example') || /\.(pem|key|p12|pfx|log)$/i.test(path)) addFinding(path, 'private-or-runtime-candidate');
    const bytes = readFileSync(absolute);
    const text = bytes.toString('utf8');
    for (const [rule, pattern] of secretRules) {
      if (pattern.test(text)) addFinding(path, rule);
    }
    entries.push({ path, state: untracked.has(path) ? 'untracked' : 'tracked', bytes: bytes.length, sha256: hash(bytes) });
  }
  const acceptance = readFileSync(resolve(root, 'ACCEPTANCE.md'), 'utf8');
  const statuses = Object.fromEntries(acceptance.split(/\r?\n/).filter(line => /^\| AC-\d\d \|/.test(line)).map(line => {
    const columns = line.split('|').slice(1, -1).map(value => value.trim());
    return [columns[0], columns.at(-1).split(/\s/)[0]];
  }));
  const expectedUnverified = new Set(['AC-01', 'AC-03', 'AC-04', 'AC-05', 'AC-14']);
  if (Object.keys(statuses).length !== 15) addFinding('ACCEPTANCE.md', 'expected-15-criteria');
  for (let i = 1; i <= 15; i++) {
    const id = `AC-${String(i).padStart(2, '0')}`;
    if (statuses[id] !== (expectedUnverified.has(id) ? 'NOT_VERIFIED' : 'PASS')) addFinding('ACCEPTANCE.md', `unexpected-status-${id}`);
  }
  const routing = JSON.parse(readFileSync(resolve(root, '.team/routing.json'), 'utf8'));
  for (const role of ['worker', 'reviewer']) {
    if (routing[role]?.harness !== 'hermes-cli-kanban') addFinding('.team/routing.json', `routing-${role}`);
  }
  if (routing.tester?.harness !== 'opencode-cli-background-service') addFinding('.team/routing.json', 'routing-tester');
  if (routing.autoDispatch !== false || routing.autoRun !== false) addFinding('.team/routing.json', 'automatic-dispatch');

  const product = entries.filter(entry => /^(backend\/|frontend\/|\.github\/|compose\.yaml$|\.env\.example$)/.test(entry.path));
  const report = {
    task: 'CHPMIS-009',
    head: git('rev-parse', 'HEAD').trim(),
    indexSha256: hash(git('ls-files', '--stage', '-z')),
    productConfigSha256: hash(product.map(entry => `${entry.path}\0${entry.sha256}`).join('\n')),
    manifestSelfExcluded: manifestPath,
    candidateCountExcludingManifest: entries.length,
    trackedCount: entries.filter(entry => entry.state === 'tracked').length,
    untrackedCountExcludingManifest: entries.filter(entry => entry.state === 'untracked').length,
    productConfigFileCount: product.length,
    acceptance: statuses,
    findings,
    scanLimit: 'Heuristic high-confidence patterns and path checks only; not a guarantee of no secrets or agency data.',
    files: entries,
  };
  if (args[0] === '--check') {
    const saved = JSON.parse(readFileSync(resolve(root, args[1]), 'utf8'));
    const mismatch = ['head', 'indexSha256', 'productConfigSha256', 'files'].filter(key => JSON.stringify(saved[key]) !== JSON.stringify(report[key]));
    if (saved.findings?.length || findings.length || mismatch.length) {
      process.stdout.write(JSON.stringify({ status: 'FAIL', mismatch, findings }, null, 2) + '\n');
      process.exitCode = 1;
    } else {
      process.stdout.write(JSON.stringify({ status: 'PASS', candidates: entries.length, productConfigFiles: product.length, indexSha256: report.indexSha256, productConfigSha256: report.productConfigSha256, findings: [] }, null, 2) + '\n');
    }
  } else {
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
    process.exitCode = findings.length ? 1 : 0;
  }
} catch {
  // Avoid leaking raw file contents or environment values in parser/subprocess errors.
  process.stderr.write('Baseline audit could not complete; check Git, candidate paths and manifest JSON.\n');
  process.exitCode = 2;
}
