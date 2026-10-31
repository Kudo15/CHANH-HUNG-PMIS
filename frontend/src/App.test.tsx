import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { isTaskOverdue } from './lib/overdue'

describe('application shell and CHPMIS-005 scoped dashboard & audit views', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input)
        if (url.includes('/api/v1/auth/session')) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                user: {
                  id: 'user-pm-01',
                  sub: 'auth0|pm01',
                  email: 'pm@chanhhung.vn',
                  name: 'Nguyễn Quản Lý',
                },
                roles: ['project_manager'],
                csrf_token: 'test-csrf-token',
              }),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/members')) {
          return Promise.resolve(
            new Response(
              JSON.stringify([
                {
                  id: 'pm-mem-1',
                  project_id: 'proj-1',
                  user_id: 'user-pm-01',
                  role: 'project_manager',
                  assigned_by: 'user-pm-01',
                  created_at: '2026-10-30T00:00:00Z',
                  updated_at: '2026-10-30T00:00:00Z',
                },
              ]),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/api/v1/projects') && !url.includes('/tasks') && !url.includes('/audit-events') && !url.includes('/members')) {
          return Promise.resolve(
            new Response(
              JSON.stringify([
                {
                  id: 'proj-1',
                  name: 'Dự án thí điểm số 1',
                  lifecycle: 'active',
                },
              ]),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/api/v1/dashboard/summary')) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                total_projects: 1,
                total_tasks: 4,
                total_overdue_tasks: 1,
                total_task_status_counts: {
                  open: 1,
                  in_progress: 1,
                  blocked: 1,
                  done: 1,
                  cancelled: 0,
                },
                projects: [
                  {
                    project_id: 'proj-1',
                    project_name: 'Dự án thí điểm số 1',
                    lifecycle: 'active',
                    task_status_counts: {
                      open: 1,
                      in_progress: 1,
                      blocked: 1,
                      done: 1,
                      cancelled: 0,
                    },
                    overdue_task_count: 1,
                    total_task_count: 4,
                  },
                ],
              }),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/tasks')) {
          return Promise.resolve(
            new Response(
              JSON.stringify([
                {
                  id: 'task-1',
                  project_id: 'proj-1',
                  title: 'Khảo sát hiện trạng',
                  status: 'open',
                  due_date: '2026-10-20T00:00:00Z',
                },
              ]),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/audit-events')) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                items: [
                  {
                    id: 'ae-1',
                    actor_id: 'user-pm-01',
                    action: 'project:create',
                    target_type: 'project',
                    target_id: 'proj-1',
                    project_id: 'proj-1',
                    correlation_id: 'corr-01',
                    created_at: '2026-10-30T10:00:00Z',
                    before_values: null,
                    after_values: { lifecycle: 'active' },
                  },
                ],
                next_cursor: null,
                has_more: false,
              }),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        return Promise.resolve(new Response(JSON.stringify({}), { status: 404 }))
      })
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders_application_shell', async () => {
    render(<App />)
    expect(screen.getByRole('heading', { level: 1, name: 'CHÁNH HƯNG PMIS' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Kiểm tra hệ thống' })).toHaveAttribute('href', '/health/ready')
    expect(
      screen.getByRole('heading', { level: 2, name: /Quản lý Dự án & Bảng điều khiển Scoped/ })
    ).toBeVisible()
    await waitFor(() => {
      expect(screen.getByText('Dự án thí điểm số 1 (active)')).toBeVisible()
    })
  })

  it('calculates isTaskOverdue with frozen time and terminal exclusion', () => {
    const frozenNow = new Date('2026-10-30T12:00:00Z')
    const pastDate = new Date('2026-10-29T12:00:00Z').toISOString()
    const futureDate = new Date('2026-10-31T12:00:00Z').toISOString()

    // Null due date is not overdue
    expect(isTaskOverdue(null, 'open', frozenNow)).toBe(false)
    expect(isTaskOverdue(undefined, 'open', frozenNow)).toBe(false)

    // Terminal statuses (done, cancelled) are excluded even if past due
    expect(isTaskOverdue(pastDate, 'done', frozenNow)).toBe(false)
    expect(isTaskOverdue(pastDate, 'cancelled', frozenNow)).toBe(false)

    // Active status past due is overdue
    expect(isTaskOverdue(pastDate, 'open', frozenNow)).toBe(true)
    expect(isTaskOverdue(pastDate, 'in_progress', frozenNow)).toBe(true)
    expect(isTaskOverdue(pastDate, 'blocked', frozenNow)).toBe(true)

    // Future due date is not overdue
    expect(isTaskOverdue(futureDate, 'open', frozenNow)).toBe(false)
  })

  it('renders scoped dashboard summary counts and overdue explanation from API', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText(/Bảng điều khiển tóm tắt:/)).toBeVisible()
    })
    expect(screen.getByTestId('count-open')).toHaveTextContent('1')
    expect(screen.getByTestId('count-in-progress')).toHaveTextContent('1')
    expect(screen.getByTestId('count-blocked')).toHaveTextContent('1')
    expect(screen.getByTestId('count-done')).toHaveTextContent('1')
    expect(screen.getByTestId('count-overdue')).toHaveTextContent('1')
    expect(screen.getByText(/Định nghĩa quá hạn:/)).toBeVisible()
  })

  it('renders scoped audit events for authorized reader', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('project:create')).toBeVisible()
    })
    expect(screen.getAllByText(/user-pm-01/)[0]).toBeVisible()
    expect(screen.getByText(/corr-01/)).toBeVisible()
  })

  it('fails closed when audit endpoint returns 404', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input)
        if (url.includes('/api/v1/auth/session')) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                user: {
                  id: 'user-pm-01',
                  sub: 'auth0|pm01',
                  email: 'pm@chanhhung.vn',
                  name: 'Nguyễn Quản Lý',
                },
                roles: ['project_manager'],
                csrf_token: 'test-csrf-token',
              }),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/members')) {
          return Promise.resolve(
            new Response(
              JSON.stringify([
                {
                  id: 'pm-mem-1',
                  project_id: 'proj-sec',
                  user_id: 'user-pm-01',
                  role: 'project_manager',
                  assigned_by: 'user-pm-01',
                  created_at: '2026-10-30T00:00:00Z',
                  updated_at: '2026-10-30T00:00:00Z',
                },
              ]),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/api/v1/projects') && !url.includes('/tasks') && !url.includes('/audit-events') && !url.includes('/members')) {
          return Promise.resolve(
            new Response(
              JSON.stringify([{ id: 'proj-sec', name: 'Dự án bí mật', lifecycle: 'active' }]),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/dashboard/summary')) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                total_projects: 1,
                total_tasks: 0,
                total_overdue_tasks: 0,
                total_task_status_counts: { open: 0, in_progress: 0, blocked: 0, done: 0, cancelled: 0 },
                projects: [{ project_id: 'proj-sec', project_name: 'Dự án bí mật', lifecycle: 'active', task_status_counts: { open: 0, in_progress: 0, blocked: 0, done: 0, cancelled: 0 }, overdue_task_count: 0, total_task_count: 0 }],
              }),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }
        if (url.includes('/audit-events')) {
          return Promise.resolve(new Response(JSON.stringify({ detail: 'Project not found' }), { status: 404 }))
        }
        return Promise.resolve(new Response(JSON.stringify([]), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      })
    )

    render(<App />)
    await waitFor(() => {
      expect(
        screen.getByText(/Không tìm thấy dự án hoặc không có quyền xem nhật ký kiểm toán/)
      ).toBeVisible()
    })
    expect(screen.queryByText('project:create')).toBeNull()
  })

  it('displays auth error when session is unauthenticated 401', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ detail: 'Authentication required' }), { status: 401 })
        )
      )
    )

    render(<App />)
    await waitFor(() => {
      expect(
        screen.getByText(/Yêu cầu phiên đăng nhập hợp lệ để truy cập dữ liệu dự án/)
      ).toBeVisible()
    })
  })
})
