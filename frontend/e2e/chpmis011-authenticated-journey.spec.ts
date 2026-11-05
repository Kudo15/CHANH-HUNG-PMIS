/**
 * CHPMIS-027 — isolated authenticated Playwright journey asset
 * (AC-14, CHPMIS-011 synthetic topology). MIXED UI/API journey — deliberately
 * labeled as such; the member-assignment step is NOT a staff-assignment UI
 * test (no such UI exists in this slice).
 *
 * Journey (PM C = positive actor, Member D = synthetic assignee):
 *   1. Fresh PM C context: safe unauthenticated negative check
 *      (`GET /api/v1/auth/session` → 401 before login), then a REAL browser
 *      login through the backend `/api/v1/auth/login` 303 redirect to the
 *      synthetic Keycloak realm (http://127.0.0.1:28081). The browser itself
 *      executes the full OIDC flow (state/nonce/PKCE/browser binding); the
 *      test only fills the credential fields. No fake sessions, no bypass.
 *   2. Fresh Member D context (separate cookie jar): same real OIDC login.
 *   3. As PM C: create a uniquely named project through the UI; add Member D
 *      through `POST /api/v1/projects/{id}/members` from the SAME authenticated
 *      browser context (real session cookie sent automatically + legitimate
 *      CSRF cookie value read in memory and passed as X-CSRF-Token); refresh
 *      project state; create a UI task assigned to D; transition it through
 *      the existing UI (open → in_progress → done); assert the project
 *      dashboard counts and audit history reflect the actions as PM C.
 *
 * Credentials are read only from process environment variables
 * CHPMIS011_PM_USERNAME / CHPMIS011_PM_PASSWORD / CHPMIS011_MEMBER_USERNAME /
 * CHPMIS011_MEMBER_PASSWORD when the E2E command is invoked. If missing, the
 * test FAILS naming the missing variable names only — it never skips, never
 * reads `.env`, and never prints values. No secret (cookies, CSRF values,
 * tokens, credentials, callback URLs, response bodies) is ever logged: all
 * assertions use non-secret fields (statuses, role names, ids, names).
 *
 * Gated runtime: this file must NOT be run without a later explicit
 * runtime/provider Human Gate, the isolated CHPMIS-023 services (backend
 * 127.0.0.1:28000, Keycloak 127.0.0.1:28081), the test-only global role
 * fixture (PM C: `project_manager`, Member D: `member`) and provisioned
 * accounts. Live execution and every runtime claim remain NOT_VERIFIED.
 * Explicitly deferred to a follow-up task (NOT claimed here): invalid /
 * replayed / swapped OIDC state and binding, inactive-user, and role/scope
 * denial cases.
 */
import { expect, test } from '@playwright/test'
import type { BrowserContext } from '@playwright/test'

const KEYCLOAK_ORIGIN = 'http://127.0.0.1:28081'
// Locked policy values from backend/app/config.py (approved security policy).
const SESSION_COOKIE_NAME = 'pmis_session'
const CSRF_COOKIE_NAME = 'pmis_csrf'

// Options for manually created contexts (config `use` options are not applied
// automatically to manual contexts): same base URL, all browser artifacts off.
const JOURNEY_CONTEXT_OPTIONS = {
  baseURL: 'http://127.0.0.1:25173',
  trace: 'off',
  video: 'off',
  screenshot: 'off',
} as const

const REQUIRED_ENV_VARS = [
  'CHPMIS011_PM_USERNAME',
  'CHPMIS011_PM_PASSWORD',
  'CHPMIS011_MEMBER_USERNAME',
  'CHPMIS011_MEMBER_PASSWORD',
] as const

function readCredentialEnv(): {
  pmUsername: string
  pmPassword: string
  memberUsername: string
  memberPassword: string
} {
  const missing = REQUIRED_ENV_VARS.filter((name) => {
    const value = process.env[name]
    return value === undefined || value.trim() === ''
  })
  if (missing.length > 0) {
    // FAIL (never skip), naming the missing variable names only — never values.
    throw new Error(
      `Missing required CHPMIS-011 environment variables: ${missing.join(', ')}. ` +
        'Supply them in the process environment of the gated E2E run; values are never logged.',
    )
  }
  return {
    pmUsername: process.env.CHPMIS011_PM_USERNAME as string,
    pmPassword: process.env.CHPMIS011_PM_PASSWORD as string,
    memberUsername: process.env.CHPMIS011_MEMBER_USERNAME as string,
    memberPassword: process.env.CHPMIS011_MEMBER_PASSWORD as string,
  }
}

function cookieAttributes(
  cookies: Array<{ name: string; secure: boolean; httpOnly: boolean; sameSite: 'Strict' | 'Lax' | 'None' }>,
  name: string,
): { present: boolean; secure: boolean; httpOnly: boolean; sameSite: 'Strict' | 'Lax' | 'None' } {
  const cookie = cookies.find((c) => c.name === name)
  return {
    present: cookie !== undefined,
    secure: cookie?.secure ?? false,
    httpOnly: cookie?.httpOnly ?? false,
    sameSite: cookie?.sameSite ?? 'None',
  }
}

/**
 * Real browser OIDC login: navigate to the backend `/login` endpoint, let the
 * browser follow the 303 redirect to Keycloak, fill the credential fields,
 * and wait for the genuine callback (the realm's sole registered redirect
 * URI) to complete with 2xx. Never fakes a session; never bypasses OIDC
 * state/nonce/PKCE/browser binding/CSRF/cookie validation.
 */
async function loginThroughKeycloakOidc(context: BrowserContext, username: string, password: string): Promise<void> {
  const page = await context.newPage()
  try {
    await page.goto('/api/v1/auth/login', { waitUntil: 'domcontentloaded', timeout: 30_000 })
    await page.waitForURL((url) => url.origin === KEYCLOAK_ORIGIN, { timeout: 30_000 })
    await page.fill('#username', username)
    await page.fill('#password', password)
    const [callbackResponse] = await Promise.all([
      page.waitForResponse(
        (response) => response.request().method() === 'GET' && response.url().includes('/api/v1/auth/callback'),
        { timeout: 60_000 },
      ),
      page.click('#kc-login'),
    ])
    // Status only: the callback URL and its query (code/state) are never logged.
    expect(callbackResponse.status(), 'the OIDC callback must complete successfully (2xx)').toBeLessThan(300)
  } finally {
    await page.close()
  }
}

/** Session endpoint through the authenticated context's API channel (Vite proxy). */
async function fetchSession(context: BrowserContext): Promise<{ userId: string; roles: string[] }> {
  const response = await context.request.get('/api/v1/auth/session')
  // The body is inspected in memory only; it is never logged.
  expect(response.status(), 'the authenticated session request must succeed (200)').toBe(200)
  const body = (await response.json()) as { user: { id: string }; roles: string[] }
  return { userId: body.user.id, roles: body.roles }
}

/** Asserts the locked cookie attribute policy without ever exposing values. */
async function assertCookieAttributes(context: BrowserContext, label: string): Promise<void> {
  const cookies = await context.cookies()
  const session = cookieAttributes(cookies, SESSION_COOKIE_NAME)
  expect(session.present, `${label}: session cookie '${SESSION_COOKIE_NAME}' must exist after the OIDC callback`).toBe(true)
  expect(session.secure, `${label}: session cookie must be Secure`).toBe(true)
  expect(session.httpOnly, `${label}: session cookie must be HttpOnly`).toBe(true)
  expect(session.sameSite, `${label}: session cookie must be SameSite=Lax`).toBe('Lax')
  const csrf = cookieAttributes(cookies, CSRF_COOKIE_NAME)
  expect(csrf.present, `${label}: CSRF cookie '${CSRF_COOKIE_NAME}' must exist after the OIDC callback`).toBe(true)
  expect(csrf.secure, `${label}: CSRF cookie must be Secure`).toBe(true)
  expect(csrf.httpOnly, `${label}: CSRF cookie must be non-HttpOnly (readable by the app)`).toBe(false)
  expect(csrf.sameSite, `${label}: CSRF cookie must be SameSite=Lax`).toBe('Lax')
}

test('CHPMIS-011 mixed UI/API journey: PM C with Member D (AC-14 asset, gated runtime)', async ({ browser, playwright }) => {
  const { pmUsername, pmPassword, memberUsername, memberPassword } = readCredentialEnv()

  // ---- PM C: fresh context; unauthenticated negative check; real OIDC login ----
  const pmContext = await browser.newContext(JOURNEY_CONTEXT_OPTIONS)

  const unauthenticated = await pmContext.request.get('/api/v1/auth/session')
  expect(unauthenticated.status(), 'an unauthenticated GET /api/v1/auth/session must return 401').toBe(401)

  await loginThroughKeycloakOidc(pmContext, pmUsername, pmPassword)
  const pmSession = await fetchSession(pmContext)
  expect(pmSession.userId, 'PM C session user id must be present').toBeTruthy()
  expect(pmSession.roles, 'PM C must hold exactly the synthetic global role "project_manager"').toEqual([
    'project_manager',
  ])
  await assertCookieAttributes(pmContext, 'PM C')

  // ---- Member D: separate fresh context (independent cookie jar), real OIDC login ----
  const memberBrowser = await playwright.chromium.launch()
  let memberUserId = ''
  try {
    const memberContext = await memberBrowser.newContext(JOURNEY_CONTEXT_OPTIONS)
    await loginThroughKeycloakOidc(memberContext, memberUsername, memberPassword)
    const memberSession = await fetchSession(memberContext)
    expect(memberSession.userId, 'Member D session user id must be present').toBeTruthy()
    expect(memberSession.roles, 'Member D must hold exactly the synthetic global role "member"').toEqual(['member'])
    await assertCookieAttributes(memberContext, 'Member D')
    memberUserId = memberSession.userId
    await memberContext.close()
  } finally {
    await memberBrowser.close()
  }

  // ---- PM C works through the application UI (25173, proxied to backend 28000) ----
  const pmPage = await pmContext.newPage()
  await pmPage.goto('/')
  // Wait until the app has loaded PM C's session (header shows name + user id).
  await pmPage.waitForFunction(
    (userId: string) => document.body.innerText.includes(userId),
    pmSession.userId,
    { timeout: 30_000 },
  )

  // 1) Create a uniquely named synthetic project through the UI.
  const uniqueName = `chpmis027-journey-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`
  const createProjectResponsePromise = pmPage.waitForResponse(
    (response) => response.request().method() === 'POST' && response.url().endsWith('/api/v1/projects'),
    { timeout: 30_000 },
  )
  await pmPage.getByRole('button', { name: 'Tạo dự án mới' }).click()
  await pmPage.fill('#create-project-name', uniqueName)
  await pmPage.getByRole('button', { name: 'Lưu dự án' }).click()
  const createProjectResponse = await createProjectResponsePromise
  expect(createProjectResponse.status(), 'project creation by PM C must succeed (201)').toBe(201)
  const createdProject = (await createProjectResponse.json()) as { id: string; name: string }
  expect(createdProject.name, 'the created project must carry the unique journey name').toBe(uniqueName)
  const projectId = createdProject.id

  // 2) MIXED UI/API STEP (not a staff-assignment UI test): add Member D via
  //    the API from the same authenticated browser context — the real session
  //    cookie is sent automatically, and the legitimate CSRF cookie value is
  //    read in memory and passed as the X-CSRF-Token header.
  const cookies = await pmContext.cookies()
  const csrfCookie = cookies.find((c) => c.name === CSRF_COOKIE_NAME)
  expect(csrfCookie, `the CSRF cookie '${CSRF_COOKIE_NAME}' must be readable from the context jar`).toBeDefined()
  if (!csrfCookie) {
    throw new Error('Unreachable: CSRF cookie guard failed')
  }
  const assignResponse = await pmContext.request.post(`/api/v1/projects/${projectId}/members`, {
    data: { user_id: memberUserId, role: 'member' },
    headers: { 'X-CSRF-Token': csrfCookie.value },
  })
  expect(assignResponse.status(), 'assigning Member D with the legitimate CSRF token must succeed (201)').toBe(201)
  const assignedMember = (await assignResponse.json()) as { user_id: string; role: string; assigned_by: string }
  expect(assignedMember.user_id).toBe(memberUserId)
  expect(assignedMember.role).toBe('member')
  expect(assignedMember.assigned_by, 'the assignment actor must be PM C').toBe(pmSession.userId)

  // 3) Refresh project state: full reload, then re-select the new project via UI.
  await pmPage.reload({ waitUntil: 'domcontentloaded' })
  await pmPage.waitForFunction(
    (userId: string) => document.body.innerText.includes(userId),
    pmSession.userId,
    { timeout: 30_000 },
  )
  await pmPage.getByRole('button', { name: uniqueName }).click()
  // The member chip renders user_id and (role) in adjacent spans with no
  // whitespace between them, so match with optional whitespace between.
  const memberChip = pmPage.getByText(new RegExp(`${memberUserId}\\s*\\(member\\)`))
  await expect(memberChip).toBeVisible()

  // 4) Create a UI task assigned to Member D (assignee options are project members).
  const taskTitle = `chpmis027 journey task ${Date.now()}`
  await expect(pmPage.getByRole('button', { name: 'Tạo công việc' })).toBeVisible()
  const createTaskResponsePromise = pmPage.waitForResponse(
    (response) =>
      response.request().method() === 'POST' && /\/api\/v1\/projects\/[^/]+\/tasks$/.test(response.url()),
    { timeout: 30_000 },
  )
  await pmPage.getByRole('button', { name: 'Tạo công việc' }).click()
  await pmPage.fill('#create-task-title', taskTitle)
  await pmPage.selectOption('#create-task-assignee', memberUserId)
  await pmPage.getByRole('button', { name: 'Lưu công việc' }).click()
  const createTaskResponse = await createTaskResponsePromise
  expect(createTaskResponse.status(), 'task creation by PM C must succeed (201)').toBe(201)
  const createdTask = (await createTaskResponse.json()) as {
    id: string
    title: string
    assignee_id: string | null
    status: string
  }
  expect(createdTask.title).toBe(taskTitle)
  expect(createdTask.assignee_id, 'the task must be assigned to Member D').toBe(memberUserId)
  expect(createdTask.status, 'a new task must start as open').toBe('open')

  // 5) Transition through the existing UI (PM C's project-manager controls):
  //    open → in_progress → done.
  const taskRow = pmPage.locator(`[data-testid="task-row-${createdTask.id}"]`)
  await expect(taskRow).toBeVisible()
  await taskRow.getByRole('button', { name: 'Bắt đầu' }).click()
  await expect(taskRow.getByRole('button', { name: 'Hoàn thành' })).toBeVisible()
  await taskRow.getByRole('button', { name: 'Hoàn thành' }).click()
  await expect(taskRow.getByRole('button', { name: 'Mở lại' })).toBeVisible()

  // 6) Project dashboard counts reflect the completed task.
  await expect(pmPage.locator('[data-testid="count-done"]')).toHaveText('1')
  await expect(pmPage.locator('[data-testid="count-open"]')).toHaveText('0')
  await expect(pmPage.locator('[data-testid="count-in-progress"]')).toHaveText('0')

  // 7) Project audit history reflects the actions with PM C as the actor.
  //    Only non-secret fields are checked (action names, actor user id).
  for (const action of ['project:create', 'project:member:assign', 'task:create', 'task:transition']) {
    const cards = pmPage.locator('div.rounded.border', {
      has: pmPage.getByText(action, { exact: true }),
    })
    expect(await cards.count(), `the project audit history must contain '${action}'`).toBeGreaterThan(0)
    expect(await cards.first().innerText(), `'${action}' must be recorded with PM C as the actor`).toContain(
      pmSession.userId,
    )
  }

  await pmPage.close()
  await pmContext.close()
})
