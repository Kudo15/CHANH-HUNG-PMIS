export function timeoutMilliseconds(value, defaultSeconds = 1800) {
  const seconds = value === undefined ? defaultSeconds : Number(value);
  if (!Number.isFinite(seconds) || seconds <= 0) {
    throw new TypeError('--timeout must be a positive finite number of seconds');
  }
  return Math.max(30, Math.floor(seconds)) * 1000;
}
