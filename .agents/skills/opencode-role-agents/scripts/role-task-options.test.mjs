import assert from 'node:assert/strict';
import test from 'node:test';
import { timeoutMilliseconds } from './role-task-options.mjs';

test('uses the documented default timeout', () => {
  assert.equal(timeoutMilliseconds(undefined), 1800_000);
});

test('clamps small positive values to the 30 second minimum', () => {
  assert.equal(timeoutMilliseconds('5'), 30_000);
});

test('rejects malformed and non-positive timeout values', () => {
  for (const value of ['abc', 'Infinity', 'NaN', '0', '-1']) {
    assert.throws(() => timeoutMilliseconds(value), /--timeout must be a positive finite number/);
  }
});
