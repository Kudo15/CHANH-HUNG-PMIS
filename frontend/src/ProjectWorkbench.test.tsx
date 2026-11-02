import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ProjectWorkbench } from './components/ProjectWorkbench'

describe('CHPMIS-007 Project Workbench', () => {
  const mockSession = {
    user: {
      id: 'user-pm-01',
      sub: 'auth0|pm01',
      email: 'pm@chanhhung.vn',
      name: 'Nguyễn Quản Lý',
      department: 'BQL',
    },
    roles: ['project_manager'],
    csrf_token: 'test-csrf-token-123',
  }

  const mockMemberSession = {
    user: {
      id: 'user-mem-02',
      sub: 'auth0|mem02',
      email: 'member@chanhhung.vn',
      name: 'Trần Thành Viên',
      department: 'Kỹ Thuật',
    },
    roles: ['member'],
    csrf_token: 'test-csrf-token-mem',
  }

  const mockAuditorSession = {
    user: {
      id: 'user-aud-03',
      sub: 'auth0|aud03',
      email: 'auditor@chanhhung.vn',
      name: 'Lê Kiểm Toán',
      department: 'Ban Kiểm Soát',
    },
    roles: ['auditor'],
    csrf_token: 'test-csrf-token-aud',
  }

  const mockProjects = [
    {
      id: 'proj-001',
      name: 'Dự án Cải tạo Thoát nước Chánh Hưng',
      description: 'Nâng cấp hệ thống cống hộp',
      lead_department_id: 'dept-01',
      project_manager_id: 'user-pm-01',
      lifecycle: 'active',
      start_date: '2026-01-01',
      end_date: '2026-12-31',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'proj-002',
      name: 'Dự án Cầu Kênh Ngang',
      description: 'Xây mới cầu dân sinh',
      lead_department_id: 'dept-02',
      project_manager_id: 'user-pm-01',
      lifecycle: 'active',
      start_date: '2026-03-01',
      end_date: '2026-09-30',
      created_at: '2026-03-01T00:00:00Z',
      updated_at: '2026-03-01T00:00:00Z',
    },
  ]

  const mockMembers = [
    {
      id: 'pm-mem-1',
      project_id: 'proj-001',
      user_id: 'user-pm-01',
      role: 'project_manager',
      assigned_by: 'user-pm-01',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'pm-mem-2',
      project_id: 'proj-001',
      user_id: 'user-mem-02',
      role: 'member',
      assigned_by: 'user-pm-01',
      created_at: '2026-01-02T00:00:00Z',
      updated_at: '2026-01-02T00:00:00Z',
    },
  ]

  const mockTasks = [
    {
      id: 'task-001',
      project_id: 'proj-001',
      title: 'Khảo sát địa chất tuyến cống',
      description: 'Khoan lấy mẫu 5 hố',
      creator_id: 'user-pm-01',
      assignee_id: 'user-mem-02',
      due_date: '2026-11-15T00:00:00Z',
      status: 'open',
      created_at: '2026-01-10T00:00:00Z',
      updated_at: '2026-01-10T00:00:00Z',
    },
    {
      id: 'task-002',
      project_id: 'proj-001',
      title: 'Thiết kế bản vẽ thi công',
      description: 'Hoàn thiện hồ sơ kỹ thuật',
      creator_id: 'user-pm-01',
      assignee_id: 'user-mem-02',
      due_date: '2026-11-30T00:00:00Z',
      status: 'in_progress',
      created_at: '2026-01-12T00:00:00Z',
      updated_at: '2026-01-12T00:00:00Z',
    },
    {
      id: 'task-003',
      project_id: 'proj-001',
      title: 'Gia cố móng cọc',
      description: 'Chờ vật tư',
      creator_id: 'user-pm-01',
      assignee_id: 'user-mem-02',
      due_date: '2026-10-01T00:00:00Z',
      status: 'blocked',
      created_at: '2026-01-15T00:00:00Z',
      updated_at: '2026-01-15T00:00:00Z',
    },
    {
      id: 'task-004',
      project_id: 'proj-001',
      title: 'Nghiệm thu giai đoạn 1',
      description: 'Đã hoàn tất kiểm tra hồ sơ',
      creator_id: 'user-pm-01',
      assignee_id: 'user-pm-01',
      due_date: '2026-09-01T00:00:00Z',
      status: 'done',
      created_at: '2026-01-05T00:00:00Z',
      updated_at: '2026-01-20T00:00:00Z',
    },
  ]

  const mockDashboard = {
    total_projects: 2,
    total_tasks: 10,
    total_overdue_tasks: 3,
    total_task_status_counts: { open: 4, in_progress: 3, blocked: 2, done: 1, cancelled: 0 },
    projects: [
      {
        project_id: 'proj-001',
        project_name: 'Dự án Cải tạo Thoát nước Chánh Hưng',
        lifecycle: 'active',
        task_status_counts: { open: 1, in_progress: 1, blocked: 1, done: 1, cancelled: 0 },
        overdue_task_count: 1,
        total_task_count: 4,
      },
      {
        project_id: 'proj-002',
        project_name: 'Dự án Cầu Kênh Ngang',
        lifecycle: 'active',
        task_status_counts: { open: 3, in_progress: 2, blocked: 1, done: 0, cancelled: 0 },
        overdue_task_count: 2,
        total_task_count: 6,
      },
    ],
  }

  const mockAuditEvents = {
    items: [
      {
        id: 'ae-001',
        actor_id: 'user-pm-01',
        action: 'project:create',
        target_type: 'project',
        target_id: 'proj-001',
        project_id: 'proj-001',
        correlation_id: 'corr-init-01',
        created_at: '2026-01-01T00:00:00Z',
        before_values: null,
        after_values: { lifecycle: 'active' },
      },
    ],
    next_cursor: null,
    has_more: false,
  }

  const setupDefaultFetchMock = (sessionOverride = mockSession) => {
    return vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      const method = init?.method?.toUpperCase() ?? 'GET'

      if (url.includes('/api/v1/auth/session')) {
        return Promise.resolve(
          new Response(JSON.stringify(sessionOverride), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      }

      if (url.endsWith('/api/v1/projects') && method === 'GET') {
        return Promise.resolve(
          new Response(JSON.stringify(mockProjects), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      }

      if (url.includes('/api/v1/projects/proj-001/members')) {
        return Promise.resolve(
          new Response(JSON.stringify(mockMembers), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      }

      if (url.includes('/api/v1/projects/proj-001/tasks') && method === 'GET') {
        return Promise.resolve(
          new Response(JSON.stringify(mockTasks), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      }

      if (url.includes('/api/v1/dashboard/summary')) {
        return Promise.resolve(
          new Response(JSON.stringify(mockDashboard), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      }

      if (url.includes('/api/v1/projects/proj-001/audit-events')) {
        return Promise.resolve(
          new Response(JSON.stringify(mockAuditEvents), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      }

      return Promise.resolve(new Response(JSON.stringify({}), { status: 404 }))
    })
  }

  beforeEach(() => {
    vi.stubGlobal('fetch', setupDefaultFetchMock())
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders unauthenticated state when session is 401', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input)
        if (url.includes('/api/v1/auth/session')) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: 'Missing session cookie' }), { status: 401 })
          )
        }
        return Promise.resolve(new Response(JSON.stringify({}), { status: 404 }))
      })
    )

    render(<ProjectWorkbench />)
    await waitFor(() => {
      expect(screen.getByText(/Yêu cầu phiên đăng nhập hợp lệ để truy cập dữ liệu dự án/)).toBeVisible()
    })
    expect(screen.queryByText('Dự án Cải tạo Thoát nước Chánh Hưng')).toBeNull()
  })

  it('renders authorized project list, user session, and selected-project metadata', async () => {
    render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByText(/Nguyễn Quản Lý/)).toBeVisible()
      expect(screen.getAllByText(/Dự án Cải tạo Thoát nước Chánh Hưng/)[0]).toBeVisible()
      expect(screen.getByText(/Dự án Cầu Kênh Ngang/)).toBeVisible()
      expect(screen.getAllByText(/user-mem-02/)[0]).toBeVisible()
    })

    // Selected project metadata
    expect(screen.getAllByText('Mã: proj-001')[0]).toBeVisible()
    expect(screen.getByText('Nâng cấp hệ thống cống hộp')).toBeVisible()

    // Member list
    expect(screen.getAllByText(/user-pm-01/)[0]).toBeVisible()
    expect(screen.getAllByText(/project_manager/)[0]).toBeVisible()
    expect(screen.getAllByText(/user-mem-02/)[0]).toBeVisible()

    // Scoped dashboard counts (proj-001: 1 open, 1 in_progress, 1 blocked, 1 done, 0 cancelled, 1 overdue)
    expect(screen.getByTestId('count-open')).toHaveTextContent('1')
    expect(screen.getByTestId('count-in-progress')).toHaveTextContent('1')
    expect(screen.getByTestId('count-blocked')).toHaveTextContent('1')
    expect(screen.getByTestId('count-done')).toHaveTextContent('1')
    expect(screen.getByTestId('count-overdue')).toHaveTextContent('1')

    // Must NOT render cross-project totals (10 total tasks, 3 overdue tasks)
    expect(screen.queryByText(/Tổng cộng 10 công việc/)).toBeNull()
  })

  it('filters project list locally with project search', async () => {
    render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getAllByText(/Dự án Cải tạo Thoát nước Chánh Hưng/)[0]).toBeVisible()
    })

    const searchInput = screen.getByPlaceholderText(/Tìm kiếm dự án/i)
    fireEvent.change(searchInput, { target: { value: 'Kênh Ngang' } })

    expect(screen.queryByText(/Dự án Cải tạo Thoát nước Chánh Hưng \(active\)/)).toBeNull()
    expect(screen.getByText(/Dự án Cầu Kênh Ngang \(active\)/)).toBeVisible()

    fireEvent.change(searchInput, { target: { value: 'Không tồn tại 999' } })
    expect(screen.getByText(/Không tìm thấy dự án phù hợp/)).toBeVisible()
  })

  it('allows global Project Manager to create a new project with CSRF token', async () => {
    const fetchMock = setupDefaultFetchMock()
    vi.stubGlobal('fetch', fetchMock)

    render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Tạo dự án mới/i })).toBeVisible()
    })

    fireEvent.click(screen.getByRole('button', { name: /Tạo dự án mới/i }))

    const nameInput = screen.getByLabelText(/Tên dự án/i)
    const descInput = screen.getByLabelText(/Mô tả/i)
    fireEvent.change(nameInput, { target: { value: 'Dự án Mới Tuyến Metro' } })
    fireEvent.change(descInput, { target: { value: 'Mô tả tuyến metro Chánh Hưng' } })

    // Mock successful project creation response
    fetchMock.mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      const method = init?.method?.toUpperCase() ?? 'GET'
      if (url.endsWith('/api/v1/projects') && method === 'POST') {
        const body = JSON.parse(String(init?.body))
        expect(init?.headers).toMatchObject({
          'X-CSRF-Token': 'test-csrf-token-123',
        })
        expect(init?.credentials).toBe('include')
        expect(body.name).toBe('Dự án Mới Tuyến Metro')
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: 'proj-003',
              name: 'Dự án Mới Tuyến Metro',
              description: 'Mô tả tuyến metro Chánh Hưng',
              lifecycle: 'active',
              project_manager_id: 'user-pm-01',
              created_at: '2026-10-30T00:00:00Z',
              updated_at: '2026-10-30T00:00:00Z',
            }),
            { status: 201, headers: { 'Content-Type': 'application/json' } }
          )
        )
      }
      return setupDefaultFetchMock()(input, init)
    })

    fireEvent.click(screen.getByRole('button', { name: /Lưu dự án/i }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/projects'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      )
    })
  })

  it('hides project creation affordance for non-PM global users', async () => {
    vi.stubGlobal('fetch', setupDefaultFetchMock(mockMemberSession))

    render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByText(/Trần Thành Viên/)).toBeVisible()
    })
    expect(screen.queryByRole('button', { name: /Tạo dự án mới/i })).toBeNull()
  })

  it('allows selected-project PM to create task with assignees restricted to project members', async () => {
    const fetchMock = setupDefaultFetchMock()
    vi.stubGlobal('fetch', fetchMock)

    render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Tạo công việc/i })).toBeVisible()
    })

    fireEvent.click(screen.getByRole('button', { name: /Tạo công việc/i }))

    const titleInput = screen.getByLabelText(/Tiêu đề công việc/i)
    const assigneeSelect = screen.getByLabelText(/Người thực hiện/i) as HTMLSelectElement

    // Check assignee options are strictly existing project members
    const optionValues = Array.from(assigneeSelect.options).map((o) => o.value)
    expect(optionValues).toContain('')
    expect(optionValues).toContain('user-pm-01')
    expect(optionValues).toContain('user-mem-02')
    expect(optionValues).not.toContain('user-outsider-99')

    fireEvent.change(titleInput, { target: { value: 'Kiểm định chất lượng bê tông' } })
    fireEvent.change(assigneeSelect, { target: { value: 'user-mem-02' } })

    fetchMock.mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      const method = init?.method?.toUpperCase() ?? 'GET'
      if (url.includes('/api/v1/projects/proj-001/tasks') && method === 'POST') {
        const body = JSON.parse(String(init?.body))
        expect(init?.headers).toMatchObject({ 'X-CSRF-Token': 'test-csrf-token-123' })
        expect(body.title).toBe('Kiểm định chất lượng bê tông')
        expect(body.assignee_id).toBe('user-mem-02')
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: 'task-005',
              project_id: 'proj-001',
              title: 'Kiểm định chất lượng bê tông',
              assignee_id: 'user-mem-02',
              status: 'open',
              creator_id: 'user-pm-01',
              created_at: '2026-10-30T00:00:00Z',
              updated_at: '2026-10-30T00:00:00Z',
            }),
            { status: 201, headers: { 'Content-Type': 'application/json' } }
          )
        )
      }
      return setupDefaultFetchMock()(input, init)
    })

    fireEvent.click(screen.getByRole('button', { name: /Lưu công việc/i }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/projects/proj-001/tasks'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  it('filters tasks locally by search keyword and status filter', async () => {
    render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByText('Khảo sát địa chất tuyến cống')).toBeVisible()
      expect(screen.getByText('Thiết kế bản vẽ thi công')).toBeVisible()
    })

    const taskSearch = screen.getByPlaceholderText(/Tìm kiếm công việc/i)
    fireEvent.change(taskSearch, { target: { value: 'địa chất' } })

    expect(screen.getByText('Khảo sát địa chất tuyến cống')).toBeVisible()
    expect(screen.queryByText('Thiết kế bản vẽ thi công')).toBeNull()

    // Reset search
    fireEvent.change(taskSearch, { target: { value: '' } })

    // Filter by status 'blocked'
    const statusFilter = screen.getByLabelText(/Lọc trạng thái/i)
    fireEvent.change(statusFilter, { target: { value: 'blocked' } })

    expect(screen.getByText('Gia cố móng cọc')).toBeVisible()
    expect(screen.queryByText('Khảo sát địa chất tuyến cống')).toBeNull()
  })

  it('enforces exact task transition matrix for assigned member vs PM vs Auditor', async () => {
    // 1. Logged in as member user-mem-02
    vi.stubGlobal('fetch', setupDefaultFetchMock(mockMemberSession))

    const { unmount: unmountMember } = render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByText('Khảo sát địa chất tuyến cống')).toBeVisible()
    })

    // task-001 is open and assigned to user-mem-02 -> can transition to in_progress
    const task1Row = screen.getByTestId('task-row-task-001')
    expect(task1Row).toHaveTextContent('Khảo sát địa chất tuyến cống')
    expect(screen.getByRole('button', { name: /Bắt đầu/i })).toBeVisible()
    // Member cannot cancel
    expect(screen.queryByRole('button', { name: /Hủy công việc/i })).toBeNull()

    // task-002 is in_progress and assigned to user-mem-02 -> can transition to blocked or done
    expect(screen.getByRole('button', { name: /Báo vướng/i })).toBeVisible()
    expect(screen.getByRole('button', { name: /Hoàn thành/i })).toBeVisible()

    // task-003 is blocked and assigned to user-mem-02 -> can transition to in_progress ("Tiếp tục")
    expect(screen.getByRole('button', { name: /Tiếp tục/i })).toBeVisible()

    // task-004 is done and assigned to user-pm-01 (not user-mem-02) -> no transitions for member
    const task4Row = screen.getByTestId('task-row-task-004')
    expect(task4Row.querySelectorAll('button').length).toBe(0)

    unmountMember()

    // 2. Logged in as Auditor -> read only, 0 transition buttons
    vi.stubGlobal('fetch', setupDefaultFetchMock(mockAuditorSession))
    const { unmount: unmountAuditor } = render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByText(/Lê Kiểm Toán/)).toBeVisible()
    })
    expect(screen.queryByRole('button', { name: /Bắt đầu/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /Báo vướng/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /Hoàn thành/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /Hủy/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /Mở lại/i })).toBeNull()

    unmountAuditor()

    // 3. Logged in as PM -> can cancel unfinished and reopen done task
    vi.stubGlobal('fetch', setupDefaultFetchMock(mockSession))
    render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByText('Khảo sát địa chất tuyến cống')).toBeVisible()
    })
    // PM can cancel task-001, task-002, task-003
    expect(screen.getAllByRole('button', { name: /Hủy/i }).length).toBeGreaterThan(0)
    // PM can reopen task-004 (done)
    expect(screen.getByRole('button', { name: /Mở lại/i })).toBeVisible()
  })

  it('allows selected-project PM to archive active project with confirmation, making it read-only', async () => {
    const fetchMock = setupDefaultFetchMock()
    vi.stubGlobal('fetch', fetchMock)

    render(<ProjectWorkbench />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Lưu trữ dự án/i })).toBeVisible()
    })

    fireEvent.click(screen.getByRole('button', { name: /Lưu trữ dự án/i }))

    // Confirmation step
    expect(screen.getByText(/Xác nhận lưu trữ dự án/i)).toBeVisible()
    expect(screen.getByRole('button', { name: /Xác nhận lưu trữ/i })).toBeVisible()

    fetchMock.mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      const method = init?.method?.toUpperCase() ?? 'GET'
      if (url.includes('/api/v1/projects/proj-001/archive') && method === 'POST') {
        expect(init?.headers).toMatchObject({ 'X-CSRF-Token': 'test-csrf-token-123' })
        expect(init?.credentials).toBe('include')
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...mockProjects[0],
              lifecycle: 'archived',
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
          )
        )
      }
      return setupDefaultFetchMock()(input, init)
    })

    fireEvent.click(screen.getByRole('button', { name: /Xác nhận lưu trữ/i }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/projects/proj-001/archive'),
        expect.objectContaining({ method: 'POST', credentials: 'include' })
      )
    })

    // Now project is archived: archive button and create task button must disappear
    await waitFor(() => {
      expect(screen.getByText(/Đã lưu trữ/i)).toBeVisible()
    })
    expect(screen.queryByRole('button', { name: /Lưu trữ dự án/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /Tạo công việc/i })).toBeNull()
  })

  describe('CHPMIS-019-F1 safe validation errors and stale project responses', () => {
    const mockMembersProj2 = [
      {
        id: 'mem-proj2-1',
        project_id: 'proj-002',
        user_id: 'user-pm-01',
        role: 'project_manager',
        assigned_by: 'user-pm-01',
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
      },
    ]

    const mockTasksProj2 = [
      {
        id: 'task-p2-01',
        project_id: 'proj-002',
        title: 'Thi công mố cầu Kênh Ngang',
        description: 'Đóng cọc mố A',
        creator_id: 'user-pm-01',
        assignee_id: 'user-pm-01',
        due_date: '2026-06-01T00:00:00Z',
        status: 'open' as const,
        created_at: '2026-03-05T00:00:00Z',
        updated_at: '2026-03-05T00:00:00Z',
      },
    ]

    const mockAuditProj2 = {
      items: [
        {
          id: 'ae-p2-01',
          actor_id: 'user-pm-01',
          action: 'project:create',
          target_type: 'project',
          target_id: 'proj-002',
          project_id: 'proj-002',
          correlation_id: 'corr-p2-01',
          created_at: '2026-03-01T00:00:00Z',
          before_values: null,
          after_values: { lifecycle: 'active' },
        },
      ],
      next_cursor: 'cursor-p2-next',
      has_more: false,
    }

    function createDeferred<T>() {
      let resolve!: (value: T | PromiseLike<T>) => void
      let reject!: (reason?: unknown) => void
      const promise = new Promise<T>((res, rej) => {
        resolve = res
        reject = rej
      })
      return { promise, resolve, reject }
    }

    it('safely handles FastAPI 422 array of validation objects without crashing React or leaking input', async () => {
      const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        const method = init?.method?.toUpperCase() ?? 'GET'

        if (url.includes('/api/v1/projects/proj-001/tasks') && method === 'POST') {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                detail: [
                  {
                    loc: ['body', 'title'],
                    msg: 'Tiêu đề không hợp lệ',
                    type: 'value_error',
                    input: 'SECRET_UNTRUSTED_INPUT_ARRAY_999',
                  },
                ],
              }),
              { status: 422, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }

        return setupDefaultFetchMock()(input, init)
      })

      vi.stubGlobal('fetch', fetchMock)
      render(<ProjectWorkbench />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Tạo công việc/i })).toBeVisible()
      })

      fireEvent.click(screen.getByRole('button', { name: /Tạo công việc/i }))
      fireEvent.change(screen.getByLabelText(/Tiêu đề công việc/i), {
        target: { value: 'Công việc test 422' },
      })
      fireEvent.click(screen.getByRole('button', { name: /Lưu công việc/i }))

      await waitFor(() => {
        expect(screen.getByText(/title: Tiêu đề không hợp lệ/i)).toBeVisible()
      })

      expect(screen.queryByText(/SECRET_UNTRUSTED_INPUT_ARRAY_999/)).toBeNull()
    })

    it('safely handles FastAPI 422 object-shaped detail and falls back for malformed shapes', async () => {
      let requestCount = 0
      const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        const method = init?.method?.toUpperCase() ?? 'GET'

        if (url.includes('/api/v1/projects/proj-001/tasks') && method === 'POST') {
          requestCount++
          if (requestCount === 1) {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  detail: {
                    loc: ['body', 'title'],
                    msg: 'Độ dài tối thiểu là 5 ký tự',
                    input: 'SECRET_UNTRUSTED_OBJECT_888',
                  },
                }),
                { status: 422, headers: { 'Content-Type': 'application/json' } }
              )
            )
          } else {
            return Promise.resolve(
              new Response(
                JSON.stringify({
                  detail: {
                    input: 'SECRET_MALFORMED_INPUT_777',
                    unknown_field: { deeply: 'nested' },
                  },
                }),
                { status: 422, headers: { 'Content-Type': 'application/json' } }
              )
            )
          }
        }

        return setupDefaultFetchMock()(input, init)
      })

      vi.stubGlobal('fetch', fetchMock)
      render(<ProjectWorkbench />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Tạo công việc/i })).toBeVisible()
      })

      // 1. Object-shaped validation error
      fireEvent.click(screen.getByRole('button', { name: /Tạo công việc/i }))
      fireEvent.change(screen.getByLabelText(/Tiêu đề công việc/i), {
        target: { value: 'Abc' },
      })
      fireEvent.click(screen.getByRole('button', { name: /Lưu công việc/i }))

      await waitFor(() => {
        expect(screen.getByText(/title: Độ dài tối thiểu là 5 ký tự/i)).toBeVisible()
      })
      expect(screen.queryByText(/SECRET_UNTRUSTED_OBJECT_888/)).toBeNull()

      // 2. Malformed shape error -> falls back to Vietnamese fallback message
      fireEvent.click(screen.getByRole('button', { name: /Lưu công việc/i }))

      await waitFor(() => {
        expect(screen.getByText('Không thể tạo công việc.')).toBeVisible()
      })
      expect(screen.queryByText(/SECRET_MALFORMED_INPUT_777/)).toBeNull()
    })

    it('ensures project A mutation refresh does not overwrite selected project B when A resolves late', async () => {
      const proj1TasksDeferred = createDeferred<Response>()
      const proj1MembersDeferred = createDeferred<Response>()
      const proj1AuditDeferred = createDeferred<Response>()
      const proj1DashDeferred = createDeferred<Response>()

      let mutationOccurred = false
      let refreshDashIntercepted = false

      const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        const method = init?.method?.toUpperCase() ?? 'GET'

        if (url.includes('/api/v1/projects/proj-001/tasks') && method === 'POST') {
          mutationOccurred = true
          return Promise.resolve(
            new Response(
              JSON.stringify({
                id: 'task-new-001',
                project_id: 'proj-001',
                title: 'Công việc mới dự án 1',
                status: 'open',
              }),
              { status: 201, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }

        // Intercept late refresh for project 1 AFTER mutation
        if (mutationOccurred && url.includes('/api/v1/projects/proj-001/tasks') && method === 'GET') {
          return proj1TasksDeferred.promise
        }
        if (mutationOccurred && url.includes('/api/v1/projects/proj-001/members')) {
          return proj1MembersDeferred.promise
        }
        if (mutationOccurred && url.includes('/api/v1/projects/proj-001/audit-events')) {
          return proj1AuditDeferred.promise
        }
        if (mutationOccurred && !refreshDashIntercepted && url.includes('/api/v1/dashboard/summary')) {
          refreshDashIntercepted = true
          return proj1DashDeferred.promise
        }

        // Project 2 endpoints
        if (url.includes('/api/v1/projects/proj-002/members')) {
          return Promise.resolve(
            new Response(JSON.stringify(mockMembersProj2), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }
        if (url.includes('/api/v1/projects/proj-002/tasks') && method === 'GET') {
          return Promise.resolve(
            new Response(JSON.stringify(mockTasksProj2), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }
        if (url.includes('/api/v1/projects/proj-002/audit-events')) {
          return Promise.resolve(
            new Response(JSON.stringify(mockAuditProj2), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }

        return setupDefaultFetchMock()(input, init)
      })

      vi.stubGlobal('fetch', fetchMock)
      render(<ProjectWorkbench />)

      // Wait for project 1 initial load
      await waitFor(() => {
        expect(screen.getByText('Khảo sát địa chất tuyến cống')).toBeVisible()
      })

      // Initiate task creation on project 1
      fireEvent.click(screen.getByRole('button', { name: /Tạo công việc/i }))
      fireEvent.change(screen.getByLabelText(/Tiêu đề công việc/i), {
        target: { value: 'Công việc mới dự án 1' },
      })
      fireEvent.click(screen.getByRole('button', { name: /Lưu công việc/i }))

      // Mutation is triggered, refreshProjectData('proj-001') is now pending on deferred promises
      await waitFor(() => {
        expect(mutationOccurred).toBe(true)
      })

      // User switches to Project B (proj-002: "Dự án Cầu Kênh Ngang")
      const proj2Button = screen.getByRole('button', { name: /Dự án Cầu Kênh Ngang/i })
      fireEvent.click(proj2Button)

      // Project B's details resolve and render
      await waitFor(() => {
        expect(screen.getByText('Thi công mố cầu Kênh Ngang')).toBeVisible()
      })
      expect(screen.queryByText('Khảo sát địa chất tuyến cống')).toBeNull()

      // Now resolve late project 1 responses
      proj1TasksDeferred.resolve(
        new Response(
          JSON.stringify([
            ...mockTasks,
            {
              id: 'task-new-001',
              project_id: 'proj-001',
              title: 'Công việc mới dự án 1',
              status: 'open',
            },
          ]),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      proj1MembersDeferred.resolve(
        new Response(JSON.stringify(mockMembers), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )
      proj1AuditDeferred.resolve(
        new Response(JSON.stringify(mockAuditEvents), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )
      proj1DashDeferred.resolve(
        new Response(JSON.stringify(mockDashboard), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )

      // Let microtasks run; project B's view must REMAIN scoped to B
      await waitFor(() => {
        expect(screen.getByText('Thi công mố cầu Kênh Ngang')).toBeVisible()
      })
      expect(screen.queryByText('Khảo sát địa chất tuyến cống')).toBeNull()
      expect(screen.queryByText('Công việc mới dự án 1')).toBeNull()
      expect(screen.queryByText('corr-init-01')).toBeNull()
      expect(screen.getByText('corr-p2-01')).toBeVisible()
    })

    it('ensures late audit pagination response for project A does not append to or overwrite selected project B', async () => {
      const proj1PaginationDeferred = createDeferred<Response>()

      const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        const method = init?.method?.toUpperCase() ?? 'GET'

        if (url.includes('/api/v1/projects/proj-001/audit-events')) {
          if (url.includes('cursor=')) {
            // Deferred pagination request
            return proj1PaginationDeferred.promise
          }
          // Initial audit request for proj-001 has more pages
          return Promise.resolve(
            new Response(
              JSON.stringify({
                ...mockAuditEvents,
                has_more: true,
                next_cursor: 'cursor-p1-page1',
              }),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            )
          )
        }

        // Project 2 endpoints
        if (url.includes('/api/v1/projects/proj-002/members')) {
          return Promise.resolve(
            new Response(JSON.stringify(mockMembersProj2), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }
        if (url.includes('/api/v1/projects/proj-002/tasks') && method === 'GET') {
          return Promise.resolve(
            new Response(JSON.stringify(mockTasksProj2), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }
        if (url.includes('/api/v1/projects/proj-002/audit-events')) {
          return Promise.resolve(
            new Response(JSON.stringify(mockAuditProj2), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        }

        return setupDefaultFetchMock()(input, init)
      })

      vi.stubGlobal('fetch', fetchMock)
      render(<ProjectWorkbench />)

      // Wait for initial load with pagination button
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Tải thêm nhật ký kiểm toán/i })).toBeVisible()
      })

      // Click load more audit on project 1
      fireEvent.click(screen.getByRole('button', { name: /Tải thêm nhật ký kiểm toán/i }))

      // Switch to project 2
      fireEvent.click(screen.getByRole('button', { name: /Dự án Cầu Kênh Ngang/i }))

      // Wait for project 2 to be rendered
      await waitFor(() => {
        expect(screen.getByText('corr-p2-01')).toBeVisible()
      })

      // Now resolve late pagination response for project 1
      proj1PaginationDeferred.resolve(
        new Response(
          JSON.stringify({
            items: [
              {
                id: 'ae-p1-page2',
                actor_id: 'user-pm-01',
                action: 'task:create',
                target_type: 'task',
                target_id: 'task-001',
                project_id: 'proj-001',
                correlation_id: 'corr-p1-page2-late',
                created_at: '2026-01-10T00:00:00Z',
                before_values: null,
                after_values: { title: 'Late task' },
              },
            ],
            next_cursor: 'cursor-p1-page2',
            has_more: false,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )

      // Project B's audit events must NOT contain project 1's late paginated item
      await waitFor(() => {
        expect(screen.getByText('corr-p2-01')).toBeVisible()
      })
      expect(screen.queryByText('corr-p1-page2-late')).toBeNull()
    })
  })
})
