/**
 * CHPMIS-027 — dedicated Playwright configuration for the isolated
 * authenticated journey asset (AC-14 / CHPMIS-011 synthetic topology).
 *
 * Selects ONLY `e2e/chpmis011-authenticated-journey.spec.ts`; the default
 * `playwright.config.ts` and `e2e/shell.spec.ts` remain untouched.
 *
 * This asset must only be executed under a later explicit runtime/provider
 * Human Gate with the isolated CHPMIS-023 topology (backend on
 * 127.0.0.1:28000, Keycloak on 127.0.0.1:28081), the test-only global role
 * fixture and provisioned runtime accounts. All live evidence remains
 * NOT_VERIFIED in this task.
 */
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: 'chpmis011-authenticated-journey.spec.ts',
  // Single journey: one worker, no retries (live failures must surface as-is).
  workers: 1,
  retries: 0,
  // The journey performs a real OIDC round trip plus several authenticated
  // UI/API steps; allow headroom beyond the 30s default.
  timeout: 120_000,
  expect: { timeout: 10_000 },
  // Terse reporter: it emits only test names/statuses and cannot emit
  // credentials, cookie values, or callback values.
  reporter: [['list']],
  use: {
    // Bundled Chromium.
    browserName: 'chromium',
    headless: true,
    baseURL: 'http://127.0.0.1:25173',
    // Browser artifacts explicitly disabled (no trace, video, or screenshots
    // to inspect or leak).
    trace: 'off',
    video: 'off',
    screenshot: 'off',
  },
  webServer: {
    command: 'npm run dev -- --port 25173',
    url: 'http://127.0.0.1:25173',
    // Unconditional: never silently reuse an existing (possibly non-isolated)
    // server on the journey port.
    reuseExistingServer: false,
    env: {
      // Injected into the spawned Vite dev server only (proxy target for
      // /api and /health per vite.config.ts). The test process itself does
      // not receive this variable.
      API_PROXY_TARGET: 'http://127.0.0.1:28000',
    },
  },
})
