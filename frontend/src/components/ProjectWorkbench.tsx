import { useEffect, useRef, useState, useTransition } from 'react'
import { formatApiError } from '../lib/apiError'

export interface User {
  id: string
  sub: string
  email: string
  name: string
  department?: string | null
}

export interface SessionData {
  user: User
  roles: string[]
  csrf_token: string
}

export interface ProjectItem {
  id: string
  name: string
  description?: string | null
  lead_department_id?: string | null
  project_manager_id?: string
  lifecycle: string
  start_date?: string | null
  end_date?: string | null
  created_at?: string
  updated_at?: string
}

export interface ProjectMember {
  id: string
  project_id: string
  user_id: string
  role: string
  assigned_by: string
  created_at: string
  updated_at: string
}

export interface TaskStatusCounts {
  open: number
  in_progress: number
  blocked: number
  done: number
  cancelled: number
}

export interface ProjectDashboardItem {
  project_id: string
  project_name: string
  lifecycle: string
  task_status_counts: TaskStatusCounts
  overdue_task_count: number
  total_task_count: number
}

export interface DashboardSummaryResponse {
  projects: ProjectDashboardItem[]
  total_projects: number
  total_tasks: number
  total_overdue_tasks: number
  total_task_status_counts: TaskStatusCounts
}

export interface TaskItem {
  id: string
  project_id: string
  title: string
  description?: string | null
  creator_id?: string
  assignee_id?: string | null
  due_date?: string | null
  status: 'open' | 'in_progress' | 'blocked' | 'done' | 'cancelled'
  created_at?: string
  updated_at?: string
}

export interface AuditEventItem {
  id: string
  actor_id: string
  action: string
  target_type: string
  target_id: string
  project_id: string
  correlation_id: string
  created_at: string
  before_values?: Record<string, unknown> | null
  after_values?: Record<string, unknown> | null
}

export interface AuditEventListResponse {
  items: AuditEventItem[]
  next_cursor: string | null
  has_more: boolean
}

export function ProjectWorkbench() {
  const [session, setSession] = useState<SessionData | null>(null)
  const [authError, setAuthError] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  const [projects, setProjects] = useState<ProjectItem[]>([])
  const [projectSearch, setProjectSearch] = useState<string>('')
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const selectedProjectIdRef = useRef<string | null>(selectedProjectId)

  useEffect(() => {
    selectedProjectIdRef.current = selectedProjectId
  }, [selectedProjectId])

  const [members, setMembers] = useState<ProjectMember[]>([])
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [taskSearch, setTaskSearch] = useState<string>('')
  const [taskStatusFilter, setTaskStatusFilter] = useState<string>('all')

  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummaryResponse | null>(null)
  const [auditEvents, setAuditEvents] = useState<AuditEventItem[]>([])
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [hasMoreAudit, setHasMoreAudit] = useState<boolean>(false)
  const [auditAccessDenied, setAuditAccessDenied] = useState<boolean>(false)

  const [actionError, setActionError] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  // Project Creation modal/form
  const [showCreateProject, setShowCreateProject] = useState<boolean>(false)
  const [projectName, setProjectName] = useState<string>('')
  const [projectDescription, setProjectDescription] = useState<string>('')
  const [projectLeadDept, setProjectLeadDept] = useState<string>('')
  const [projectStartDate, setProjectStartDate] = useState<string>('')
  const [projectEndDate, setProjectEndDate] = useState<string>('')
  const [isSubmittingProject, setIsSubmittingProject] = useState<boolean>(false)

  // Task Creation modal/form
  const [showCreateTask, setShowCreateTask] = useState<boolean>(false)
  const [taskTitle, setTaskTitle] = useState<string>('')
  const [taskDescription, setTaskDescription] = useState<string>('')
  const [taskAssigneeId, setTaskAssigneeId] = useState<string>('')
  const [taskDueDate, setTaskDueDate] = useState<string>('')
  const [isSubmittingTask, setIsSubmittingTask] = useState<boolean>(false)

  // Archive Confirmation
  const [confirmingArchive, setConfirmingArchive] = useState<boolean>(false)
  const [isArchiving, setIsArchiving] = useState<boolean>(false)

  const [, startTransition] = useTransition()

  // 1. Load Session & Authorized Projects on mount
  useEffect(() => {
    let ignore = false

    async function loadSessionAndProjects() {
      try {
        setLoading(true)
        const sessionRes = await fetch('/api/v1/auth/session', { credentials: 'include' })

        if (ignore) return

        if (!sessionRes.ok) {
          setAuthError('Yêu cầu phiên đăng nhập hợp lệ để truy cập dữ liệu dự án.')
          setLoading(false)
          return
        }

        const sessionData: SessionData = await sessionRes.json()
        if (ignore) return
        setSession(sessionData)

        // Fetch authorized projects and dashboard summary
        const [projRes, dashRes] = await Promise.all([
          fetch('/api/v1/projects', { credentials: 'include' }),
          fetch('/api/v1/dashboard/summary', { credentials: 'include' }),
        ])
        if (ignore) return

        if (!projRes.ok) {
          if (projRes.status === 401) {
            setAuthError('Yêu cầu phiên đăng nhập hợp lệ để truy cập dữ liệu dự án.')
          } else {
            setAuthError('Không thể tải danh sách dự án.')
          }
          setLoading(false)
          return
        }

        const projData: ProjectItem[] = await projRes.json()
        if (ignore) return
        setProjects(projData)
        if (projData.length > 0) {
          setSelectedProjectId((prev) => prev ?? projData[0].id)
        }

        if (dashRes.ok) {
          const dashData: DashboardSummaryResponse = await dashRes.json()
          if (!ignore) {
            setDashboardSummary(dashData)
          }
        }
      } catch {
        if (!ignore) {
          setAuthError('Không thể kết nối đến máy chủ PMIS.')
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    void loadSessionAndProjects()
    return () => {
      ignore = true
    }
  }, [])

  // 2. Load Selected Project details (members, tasks, dashboard, audit)
  const refreshProjectData = async (projectId: string) => {
    try {
      const [membersRes, tasksRes, dashRes, auditRes] = await Promise.all([
        fetch(`/api/v1/projects/${projectId}/members`, { credentials: 'include' }),
        fetch(`/api/v1/projects/${projectId}/tasks`, { credentials: 'include' }),
        fetch('/api/v1/dashboard/summary', { credentials: 'include' }),
        fetch(`/api/v1/projects/${projectId}/audit-events?limit=20`, { credentials: 'include' }),
      ])

      if (selectedProjectIdRef.current !== projectId) return

      if (membersRes.ok) {
        const membersData: ProjectMember[] = await membersRes.json()
        if (selectedProjectIdRef.current !== projectId) return
        setMembers(membersData)
      } else {
        if (selectedProjectIdRef.current !== projectId) return
        setMembers([])
      }

      if (tasksRes.ok) {
        const tasksData: TaskItem[] = await tasksRes.json()
        if (selectedProjectIdRef.current !== projectId) return
        setTasks(tasksData)
      } else {
        if (selectedProjectIdRef.current !== projectId) return
        setTasks([])
      }

      if (dashRes.ok) {
        const dashData: DashboardSummaryResponse = await dashRes.json()
        if (selectedProjectIdRef.current !== projectId) return
        setDashboardSummary(dashData)
      }

      if (auditRes.ok) {
        const auditData: AuditEventListResponse = await auditRes.json()
        if (selectedProjectIdRef.current !== projectId) return
        setAuditEvents(auditData.items)
        setNextCursor(auditData.next_cursor)
        setHasMoreAudit(auditData.has_more)
        setAuditAccessDenied(false)
      } else {
        if (selectedProjectIdRef.current !== projectId) return
        setAuditEvents([])
        setNextCursor(null)
        setHasMoreAudit(false)
        setAuditAccessDenied(true)
      }
    } catch {
      if (selectedProjectIdRef.current !== projectId) return
      setMembers([])
      setTasks([])
      setAuditEvents([])
      setAuditAccessDenied(true)
    }
  }

  useEffect(() => {
    let ignore = false

    async function loadSelectedProject(projectId: string | null) {
      if (!projectId) {
        setMembers([])
        setTasks([])
        setAuditEvents([])
        return
      }

      try {
        const [membersRes, tasksRes, dashRes, auditRes] = await Promise.all([
          fetch(`/api/v1/projects/${projectId}/members`, { credentials: 'include' }),
          fetch(`/api/v1/projects/${projectId}/tasks`, { credentials: 'include' }),
          fetch('/api/v1/dashboard/summary', { credentials: 'include' }),
          fetch(`/api/v1/projects/${projectId}/audit-events?limit=20`, { credentials: 'include' }),
        ])

        if (ignore) return

        if (membersRes.ok) {
          const membersData: ProjectMember[] = await membersRes.json()
          if (!ignore) setMembers(membersData)
        } else if (!ignore) {
          setMembers([])
        }

        if (tasksRes.ok) {
          const tasksData: TaskItem[] = await tasksRes.json()
          if (!ignore) setTasks(tasksData)
        } else if (!ignore) {
          setTasks([])
        }

        if (dashRes.ok) {
          const dashData: DashboardSummaryResponse = await dashRes.json()
          if (!ignore) setDashboardSummary(dashData)
        }

        if (auditRes.ok) {
          const auditData: AuditEventListResponse = await auditRes.json()
          if (!ignore) {
            setAuditEvents(auditData.items)
            setNextCursor(auditData.next_cursor)
            setHasMoreAudit(auditData.has_more)
            setAuditAccessDenied(false)
          }
        } else if (!ignore) {
          setAuditEvents([])
          setNextCursor(null)
          setHasMoreAudit(false)
          setAuditAccessDenied(true)
        }
      } catch {
        if (!ignore) {
          setMembers([])
          setTasks([])
          setAuditEvents([])
          setAuditAccessDenied(true)
        }
      }
    }

    void loadSelectedProject(selectedProjectId)

    return () => {
      ignore = true
    }
  }, [selectedProjectId])

  // Derived selected project & current user project role
  const selectedProject = projects.find((p) => p.id === selectedProjectId)
  const currentMember = members.find((m) => m.user_id === session?.user?.id)
  const currentProjectRole = currentMember?.role ?? null
  const isGlobalPM = session?.roles?.includes('project_manager') ?? false
  const isProjectPM = currentProjectRole === 'project_manager'
  const isProjectArchived = selectedProject?.lifecycle === 'archived'

  // Selected project dashboard summary (ONLY matching selected project, NO cross-project totals!)
  const selectedDashboard = dashboardSummary?.projects.find((p) => p.project_id === selectedProjectId)

  // Filtered projects
  const filteredProjects = projects.filter((p) => {
    if (!projectSearch.trim()) return true
    const term = projectSearch.toLowerCase()
    return p.name.toLowerCase().includes(term) || p.id.toLowerCase().includes(term)
  })

  // Filtered tasks
  const filteredTasks = tasks.filter((t) => {
    const matchesSearch = !taskSearch.trim() || t.title.toLowerCase().includes(taskSearch.toLowerCase())
    const matchesStatus = taskStatusFilter === 'all' || t.status === taskStatusFilter
    return matchesSearch && matchesStatus
  })

  // Load more audit events
  const handleLoadMoreAudit = async () => {
    if (!selectedProjectId || !nextCursor) return
    const currentProject = selectedProjectId
    try {
      const auditRes = await fetch(
        `/api/v1/projects/${currentProject}/audit-events?limit=20&cursor=${encodeURIComponent(nextCursor)}`,
        { credentials: 'include' }
      )
      if (selectedProjectIdRef.current !== currentProject) return
      if (auditRes.ok) {
        const auditData: AuditEventListResponse = await auditRes.json()
        if (selectedProjectIdRef.current !== currentProject) return
        setAuditEvents((prev) => [...prev, ...auditData.items])
        setNextCursor(auditData.next_cursor)
        setHasMoreAudit(auditData.has_more)
      }
    } catch {
      // non-fatal
    }
  }

  // Create Project handler
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!session?.csrf_token) {
      setActionError('Thiếu token CSRF bảo mật.')
      return
    }
    if (!projectName.trim()) {
      setActionError('Tên dự án không được để trống.')
      return
    }

    try {
      setIsSubmittingProject(true)
      setActionError(null)

      const payload = {
        name: projectName.trim(),
        description: projectDescription.trim() || null,
        lead_department_id: projectLeadDept.trim() || null,
        start_date: projectStartDate || null,
        end_date: projectEndDate || null,
      }

      const res = await fetch('/api/v1/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': session.csrf_token,
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => null)
        setActionError(formatApiError(errorData?.detail ?? errorData, 'Không thể tạo dự án.'))
        return
      }

      const newProject: ProjectItem = await res.json()
      setActionSuccess(`Đã tạo dự án thành công: ${newProject.name}`)
      setProjectName('')
      setProjectDescription('')
      setProjectLeadDept('')
      setProjectStartDate('')
      setProjectEndDate('')
      setShowCreateProject(false)

      setProjects((prev) => [...prev, newProject])
      setSelectedProjectId(newProject.id)
    } catch {
      setActionError('Lỗi kết nối máy chủ khi tạo dự án.')
    } finally {
      setIsSubmittingProject(false)
    }
  }

  // Create Task handler
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedProjectId || !session?.csrf_token) {
      setActionError('Thiếu thông tin phiên hoặc dự án.')
      return
    }
    if (!taskTitle.trim()) {
      setActionError('Tiêu đề công việc không được để trống.')
      return
    }

    const currentProjectId = selectedProjectId

    try {
      setIsSubmittingTask(true)
      setActionError(null)

      const payload = {
        title: taskTitle.trim(),
        description: taskDescription.trim() || null,
        assignee_id: taskAssigneeId.trim() || null,
        due_date: taskDueDate ? new Date(taskDueDate).toISOString() : null,
      }

      const res = await fetch(`/api/v1/projects/${currentProjectId}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': session.csrf_token,
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => null)
        setActionError(formatApiError(errorData?.detail ?? errorData, 'Không thể tạo công việc.'))
        return
      }

      const createdTask: TaskItem = await res.json()
      setActionSuccess(`Đã tạo công việc: ${createdTask.title}`)
      setTaskTitle('')
      setTaskDescription('')
      setTaskAssigneeId('')
      setTaskDueDate('')
      setShowCreateTask(false)

      await refreshProjectData(currentProjectId)
    } catch {
      setActionError('Lỗi kết nối máy chủ khi tạo công việc.')
    } finally {
      setIsSubmittingTask(false)
    }
  }

  // Task Status Transition handler
  const handleTransitionTask = async (
    taskId: string,
    targetStatus: 'in_progress' | 'blocked' | 'done' | 'cancelled'
  ) => {
    if (!selectedProjectId || !session?.csrf_token) {
      setActionError('Thiếu thông tin phiên bảo mật.')
      return
    }

    const currentProjectId = selectedProjectId

    try {
      setActionError(null)
      const res = await fetch(`/api/v1/tasks/${taskId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': session.csrf_token,
        },
        credentials: 'include',
        body: JSON.stringify({ status: targetStatus }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => null)
        setActionError(formatApiError(err?.detail ?? err, 'Chuyển trạng thái công việc thất bại.'))
        return
      }

      setActionSuccess(`Đã cập nhật trạng thái công việc sang: ${targetStatus}`)
      await refreshProjectData(currentProjectId)
    } catch {
      setActionError('Lỗi kết nối khi cập nhật trạng thái công việc.')
    }
  }

  // Archive Project handler
  const handleArchiveProject = async () => {
    if (!selectedProjectId || !session?.csrf_token) {
      setActionError('Thiếu thông tin phiên hoặc dự án.')
      return
    }

    const currentProjectId = selectedProjectId

    try {
      setIsArchiving(true)
      setActionError(null)

      const res = await fetch(`/api/v1/projects/${currentProjectId}/archive`, {
        method: 'POST',
        headers: {
          'X-CSRF-Token': session.csrf_token,
        },
        credentials: 'include',
      })

      if (!res.ok) {
        const err = await res.json().catch(() => null)
        setActionError(formatApiError(err?.detail ?? err, 'Không thể lưu trữ dự án.'))
        return
      }

      const updatedProject: ProjectItem = await res.json()
      setActionSuccess('Dự án đã được lưu trữ thành công.')
      setConfirmingArchive(false)
      setProjects((prev) => prev.map((p) => (p.id === updatedProject.id ? updatedProject : p)))
      await refreshProjectData(currentProjectId)
    } catch {
      setActionError('Lỗi kết nối máy chủ khi lưu trữ dự án.')
    } finally {
      setIsArchiving(false)
    }
  }

  return (
    <section className="mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Quản lý Dự án & Bảng điều khiển Scoped (CHPMIS-005 / CHPMIS-007)
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Bàn làm việc dự án cho nhân viên có thẩm quyền: tổng quan dự án, phân công công việc, và truy vết kiểm toán.
          </p>
        </div>
        <div className="text-right text-xs text-slate-500">
          {session?.user ? (
            <div>
              <span className="font-semibold text-slate-800">{session.user.name}</span> ({session.user.id})
              <div className="text-slate-400">
                Vai trò toàn cục: {session.roles.length > 0 ? session.roles.join(', ') : 'Người dùng'}
              </div>
            </div>
          ) : (
            <div>
              Xác thực: <span className="font-semibold text-slate-700">Phiên HTTP-only Cookie</span>
            </div>
          )}
        </div>
      </div>

      {/* Notifications / Feedback */}
      {authError && (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800" role="alert">
          {authError}
        </div>
      )}

      {actionError && (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">
          {actionError}
        </div>
      )}

      {actionSuccess && (
        <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800" role="alert">
          {actionSuccess}
        </div>
      )}

      {loading && !authError && (
        <p className="mt-4 text-sm text-slate-400">Đang tải dữ liệu từ máy chủ...</p>
      )}

      {!loading && !authError && (
        <>
          {/* Top Action Bar: Search & Global PM Create Project */}
          <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
            <div className="flex-1 min-w-[240px] max-w-md">
              <label htmlFor="project-search" className="sr-only">Tìm kiếm dự án</label>
              <input
                id="project-search"
                type="text"
                placeholder="Tìm kiếm dự án (tên hoặc mã)..."
                value={projectSearch}
                onChange={(e) => setProjectSearch(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm placeholder-slate-400 focus:border-slate-500 focus:outline-none"
              />
            </div>

            {isGlobalPM && (
              <button
                onClick={() => setShowCreateProject(!showCreateProject)}
                className="bg-blue-600 text-white hover:bg-blue-700"
              >
                {showCreateProject ? 'Đóng biểu mẫu' : 'Tạo dự án mới'}
              </button>
            )}
          </div>

          {/* Create Project Form (Global PM only) */}
          {showCreateProject && isGlobalPM && (
            <form onSubmit={handleCreateProject} className="mt-4 rounded-md border border-blue-200 bg-blue-50/50 p-4">
              <h3 className="text-sm font-bold text-blue-900">Tạo dự án mới</h3>
              <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="create-project-name" className="block text-xs font-medium text-slate-700">
                    Tên dự án *
                  </label>
                  <input
                    id="create-project-name"
                    type="text"
                    required
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label htmlFor="create-project-desc" className="block text-xs font-medium text-slate-700">
                    Mô tả
                  </label>
                  <textarea
                    id="create-project-desc"
                    rows={2}
                    value={projectDescription}
                    onChange={(e) => setProjectDescription(e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="create-project-dept" className="block text-xs font-medium text-slate-700">
                    Mã phòng ban chủ trì
                  </label>
                  <input
                    id="create-project-dept"
                    type="text"
                    value={projectLeadDept}
                    onChange={(e) => setProjectLeadDept(e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label htmlFor="create-project-start" className="block text-xs font-medium text-slate-700">
                      Ngày bắt đầu
                    </label>
                    <input
                      id="create-project-start"
                      type="date"
                      value={projectStartDate}
                      onChange={(e) => setProjectStartDate(e.target.value)}
                      className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="create-project-end" className="block text-xs font-medium text-slate-700">
                      Ngày kết thúc
                    </label>
                    <input
                      id="create-project-end"
                      type="date"
                      value={projectEndDate}
                      onChange={(e) => setProjectEndDate(e.target.value)}
                      className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                    />
                  </div>
                </div>
              </div>
              <div className="mt-4 flex justify-end gap-2">
                <button
                  type="button"
                  
                  onClick={() => setShowCreateProject(false)}
                >
                  Hủy
                </button>
                <button type="submit" disabled={isSubmittingProject}>
                  {isSubmittingProject ? 'Đang lưu...' : 'Lưu dự án'}
                </button>
              </div>
            </form>
          )}

          {/* Authorized Projects Navigation */}
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-slate-700">Danh sách dự án được phân công</h3>
            {projects.length === 0 ? (
              <p className="mt-2 text-sm text-slate-400">Bạn chưa được phân công vào dự án nào.</p>
            ) : filteredProjects.length === 0 ? (
              <p className="mt-2 text-sm text-slate-400">Không tìm thấy dự án phù hợp với từ khóa tìm kiếm.</p>
            ) : (
              <div className="mt-2 flex flex-wrap gap-2">
                {filteredProjects.map((proj) => (
                  <button
                    key={proj.id}
                    onClick={() => {
                      startTransition(() => {
                        setSelectedProjectId(proj.id)
                        setConfirmingArchive(false)
                        setShowCreateTask(false)
                      })
                    }}
                    className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                      selectedProjectId === proj.id
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {proj.name} ({proj.lifecycle})
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Selected Project Workspace */}
          {selectedProject && (
            <div className="mt-8 space-y-6">
              {/* Selected Project Overview Card */}
              <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-slate-900">{selectedProject.name}</h3>
                      <span
                        className={`rounded px-2.5 py-0.5 text-xs font-semibold ${
                          isProjectArchived
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {isProjectArchived ? 'Đã lưu trữ (Chỉ đọc)' : selectedProject.lifecycle}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">Mã: {selectedProject.id}</p>
                    {selectedProject.description && (
                      <p className="mt-2 text-sm text-slate-600">{selectedProject.description}</p>
                    )}
                  </div>

                  {/* Project Archive Action (Project Manager & Active only) */}
                  {isProjectPM && !isProjectArchived && (
                    <div>
                      {!confirmingArchive ? (
                        <button
                          
                          onClick={() => setConfirmingArchive(true)}
                          className="text-xs"
                        >
                          Lưu trữ dự án
                        </button>
                      ) : (
                        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-xs">
                          <p className="font-semibold text-red-800">Xác nhận lưu trữ dự án?</p>
                          <p className="mt-1 text-red-600">Dự án sẽ chuyển sang chỉ đọc sau khi lưu trữ.</p>
                          <div className="mt-2 flex gap-2">
                            <button
                              
                              disabled={isArchiving}
                              onClick={handleArchiveProject}
                              className="text-xs py-1 h-7"
                            >
                              {isArchiving ? 'Đang lưu trữ...' : 'Xác nhận lưu trữ'}
                            </button>
                            <button
                              
                              onClick={() => setConfirmingArchive(false)}
                              className="text-xs py-1 h-7"
                            >
                              Hủy
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Project Role Badge & Members */}
                <div className="mt-4 border-t border-slate-200 pt-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div>
                      <span className="font-medium text-slate-500">Vai trò của bạn trong dự án: </span>
                      <span className="font-bold text-slate-800">
                        {currentProjectRole ? currentProjectRole : 'Không thuộc thành viên'}
                      </span>
                    </div>
                  </div>

                  <div className="mt-2">
                    <span className="text-xs font-semibold text-slate-600">Thành viên dự án: </span>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {members.map((m) => (
                        <span
                          key={m.id}
                          className="inline-flex items-center gap-1 rounded bg-white px-2 py-1 text-xs border border-slate-200 font-mono text-slate-700"
                        >
                          <span className="font-bold">{m.user_id}</span>
                          <span className="text-slate-400">({m.role})</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Scoped Dashboard Summary (Project scoped only, no cross-project totals!) */}
              <div className="rounded-md bg-slate-50 p-4 border border-slate-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
                    Bảng điều khiển tóm tắt: <span className="text-blue-700">{selectedProject.name}</span>
                  </h3>
                  <span className="text-xs text-slate-500">Mã: {selectedProject.id}</span>
                </div>

                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-6 text-center">
                  <div className="rounded bg-white p-2.5 shadow-sm border border-slate-200">
                    <span className="block text-xs font-medium text-slate-500">Mở</span>
                    <span className="text-lg font-bold text-slate-800" data-testid="count-open">
                      {selectedDashboard?.task_status_counts.open ?? 0}
                    </span>
                  </div>
                  <div className="rounded bg-white p-2.5 shadow-sm border border-slate-200">
                    <span className="block text-xs font-medium text-slate-500">Đang làm</span>
                    <span className="text-lg font-bold text-blue-600" data-testid="count-in-progress">
                      {selectedDashboard?.task_status_counts.in_progress ?? 0}
                    </span>
                  </div>
                  <div className="rounded bg-white p-2.5 shadow-sm border border-slate-200">
                    <span className="block text-xs font-medium text-slate-500">Vướng mắc</span>
                    <span className="text-lg font-bold text-amber-600" data-testid="count-blocked">
                      {selectedDashboard?.task_status_counts.blocked ?? 0}
                    </span>
                  </div>
                  <div className="rounded bg-white p-2.5 shadow-sm border border-slate-200">
                    <span className="block text-xs font-medium text-slate-500">Hoàn thành</span>
                    <span className="text-lg font-bold text-emerald-600" data-testid="count-done">
                      {selectedDashboard?.task_status_counts.done ?? 0}
                    </span>
                  </div>
                  <div className="rounded bg-white p-2.5 shadow-sm border border-slate-200">
                    <span className="block text-xs font-medium text-slate-500">Đã hủy</span>
                    <span className="text-lg font-bold text-slate-400" data-testid="count-cancelled">
                      {selectedDashboard?.task_status_counts.cancelled ?? 0}
                    </span>
                  </div>
                  <div className="rounded bg-white p-2.5 shadow-sm border border-red-200 bg-red-50">
                    <span className="block text-xs font-medium text-red-700">Quá hạn</span>
                    <span className="text-lg font-bold text-red-700" data-testid="count-overdue">
                      {selectedDashboard?.overdue_task_count ?? 0}
                    </span>
                  </div>
                </div>

                <p className="mt-2.5 text-xs text-slate-500 italic">
                  * Định nghĩa quá hạn: Công việc có ngày hết hạn trước thời điểm hiện tại và trạng thái chưa hoàn thành hoặc đã hủy.
                </p>
              </div>

              {/* Tasks Section */}
              <div className="border-t border-slate-200 pt-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h3 className="text-base font-semibold text-slate-800">
                      Danh sách công việc: <span className="font-bold">{selectedProject.name}</span>
                    </h3>
                    <p className="text-xs text-slate-500">
                      Hiển thị {filteredTasks.length}/{tasks.length} công việc
                    </p>
                  </div>

                  {/* Task creation button (Project PM & Active project only) */}
                  {isProjectPM && !isProjectArchived && (
                    <button
                      onClick={() => setShowCreateTask(!showCreateTask)}
                      className="bg-emerald-600 text-white hover:bg-emerald-700 text-xs"
                    >
                      {showCreateTask ? 'Đóng biểu mẫu' : 'Tạo công việc'}
                    </button>
                  )}
                </div>

                {/* Create Task Form */}
                {showCreateTask && isProjectPM && !isProjectArchived && (
                  <form onSubmit={handleCreateTask} className="mt-4 rounded-md border border-emerald-200 bg-emerald-50/40 p-4">
                    <h4 className="text-sm font-bold text-emerald-900">Tạo công việc mới</h4>
                    <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <div className="sm:col-span-2">
                        <label htmlFor="create-task-title" className="block text-xs font-medium text-slate-700">
                          Tiêu đề công việc *
                        </label>
                        <input
                          id="create-task-title"
                          type="text"
                          required
                          value={taskTitle}
                          onChange={(e) => setTaskTitle(e.target.value)}
                          className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <label htmlFor="create-task-desc" className="block text-xs font-medium text-slate-700">
                          Mô tả chi tiết
                        </label>
                        <textarea
                          id="create-task-desc"
                          rows={2}
                          value={taskDescription}
                          onChange={(e) => setTaskDescription(e.target.value)}
                          className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                        />
                      </div>
                      <div>
                        <label htmlFor="create-task-assignee" className="block text-xs font-medium text-slate-700">
                          Người thực hiện (Giới hạn trong thành viên dự án)
                        </label>
                        <select
                          id="create-task-assignee"
                          value={taskAssigneeId}
                          onChange={(e) => setTaskAssigneeId(e.target.value)}
                          className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                        >
                          <option value="">Chưa phân công</option>
                          {members.map((m) => (
                            <option key={m.id} value={m.user_id}>
                              {m.user_id} ({m.role})
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label htmlFor="create-task-due" className="block text-xs font-medium text-slate-700">
                          Hạn hoàn thành
                        </label>
                        <input
                          id="create-task-due"
                          type="date"
                          value={taskDueDate}
                          onChange={(e) => setTaskDueDate(e.target.value)}
                          className="mt-1 w-full rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
                        />
                      </div>
                    </div>
                    <div className="mt-4 flex justify-end gap-2">
                      <button
                        type="button"
                        
                        onClick={() => setShowCreateTask(false)}
                      >
                        Hủy
                      </button>
                      <button type="submit" disabled={isSubmittingTask}>
                        {isSubmittingTask ? 'Đang lưu...' : 'Lưu công việc'}
                      </button>
                    </div>
                  </form>
                )}

                {/* Task Search & Filter Controls */}
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <div className="flex-1 min-w-[200px]">
                    <label htmlFor="task-search-input" className="sr-only">Tìm kiếm công việc</label>
                    <input
                      id="task-search-input"
                      type="text"
                      placeholder="Tìm kiếm công việc theo tiêu đề..."
                      value={taskSearch}
                      onChange={(e) => setTaskSearch(e.target.value)}
                      className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs placeholder-slate-400"
                    />
                  </div>
                  <div>
                    <label htmlFor="task-status-filter" className="sr-only">Lọc trạng thái</label>
                    <select
                      id="task-status-filter"
                      aria-label="Lọc trạng thái"
                      value={taskStatusFilter}
                      onChange={(e) => setTaskStatusFilter(e.target.value)}
                      className="rounded border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-700"
                    >
                      <option value="all">Tất cả trạng thái</option>
                      <option value="open">Mở (open)</option>
                      <option value="in_progress">Đang làm (in_progress)</option>
                      <option value="blocked">Vướng mắc (blocked)</option>
                      <option value="done">Hoàn thành (done)</option>
                      <option value="cancelled">Đã hủy (cancelled)</option>
                    </select>
                  </div>
                </div>

                {/* Task List */}
                <div className="mt-4 space-y-2">
                  {tasks.length === 0 ? (
                    <p className="text-sm text-slate-400">Chưa có công việc nào trong dự án này.</p>
                  ) : filteredTasks.length === 0 ? (
                    <p className="text-sm text-slate-400">Không tìm thấy công việc phù hợp với bộ lọc.</p>
                  ) : (
                    filteredTasks.map((t) => {
                      const isAssigned = t.assignee_id === session?.user?.id

                      return (
                        <div
                          key={t.id}
                          data-testid={`task-row-${t.id}`}
                          className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-200 p-3 bg-white"
                        >
                          <div>
                            <p className="text-sm font-medium text-slate-900">{t.title}</p>
                            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
                              <span
                                className={`inline-block rounded px-2 py-0.5 font-semibold ${
                                  t.status === 'open'
                                    ? 'bg-slate-100 text-slate-700'
                                    : t.status === 'in_progress'
                                    ? 'bg-blue-100 text-blue-800'
                                    : t.status === 'blocked'
                                    ? 'bg-amber-100 text-amber-800'
                                    : t.status === 'done'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-slate-100 text-slate-400'
                                }`}
                              >
                                {t.status}
                              </span>
                              <span className="text-slate-500">
                                Người thực hiện: {t.assignee_id ? t.assignee_id : 'Chưa phân công'}
                              </span>
                              {t.due_date && (
                                <span className="text-slate-500">
                                  Hạn: {new Date(t.due_date).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Task Action Controls adhering to exact Matrix */}
                          {!isProjectArchived && t.status !== 'cancelled' && currentProjectRole !== 'auditor' && (
                            <div className="flex flex-wrap items-center gap-1.5">
                              {/* Member transitions (only own assigned task) */}
                              {currentProjectRole === 'member' && isAssigned && (
                                <>
                                  {t.status === 'open' && (
                                    <button
                                      
                                      
                                      onClick={() => handleTransitionTask(t.id, 'in_progress')}
                                      className="text-xs h-7 px-2"
                                    >
                                      Bắt đầu
                                    </button>
                                  )}
                                  {t.status === 'in_progress' && (
                                    <>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'blocked')}
                                        className="text-xs h-7 px-2 text-amber-700 border-amber-300"
                                      >
                                        Báo vướng
                                      </button>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'done')}
                                        className="text-xs h-7 px-2 text-emerald-700 border-emerald-300"
                                      >
                                        Hoàn thành
                                      </button>
                                    </>
                                  )}
                                  {t.status === 'blocked' && (
                                    <button
                                      
                                      
                                      onClick={() => handleTransitionTask(t.id, 'in_progress')}
                                      className="text-xs h-7 px-2"
                                    >
                                      Tiếp tục
                                    </button>
                                  )}
                                </>
                              )}

                              {/* Project Manager transitions */}
                              {isProjectPM && (
                                <>
                                  {t.status === 'open' && (
                                    <>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'in_progress')}
                                        className="text-xs h-7 px-2"
                                      >
                                        Bắt đầu
                                      </button>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'cancelled')}
                                        className="text-xs h-7 px-2 text-slate-500"
                                      >
                                        Hủy
                                      </button>
                                    </>
                                  )}
                                  {t.status === 'in_progress' && (
                                    <>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'blocked')}
                                        className="text-xs h-7 px-2 text-amber-700 border-amber-300"
                                      >
                                        Báo vướng
                                      </button>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'done')}
                                        className="text-xs h-7 px-2 text-emerald-700 border-emerald-300"
                                      >
                                        Hoàn thành
                                      </button>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'cancelled')}
                                        className="text-xs h-7 px-2 text-slate-500"
                                      >
                                        Hủy
                                      </button>
                                    </>
                                  )}
                                  {t.status === 'blocked' && (
                                    <>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'in_progress')}
                                        className="text-xs h-7 px-2"
                                      >
                                        Tiếp tục
                                      </button>
                                      <button
                                        
                                        
                                        onClick={() => handleTransitionTask(t.id, 'cancelled')}
                                        className="text-xs h-7 px-2 text-slate-500"
                                      >
                                        Hủy
                                      </button>
                                    </>
                                  )}
                                  {t.status === 'done' && (
                                    <button
                                      
                                      
                                      onClick={() => handleTransitionTask(t.id, 'in_progress')}
                                      className="text-xs h-7 px-2"
                                    >
                                      Mở lại
                                    </button>
                                  )}
                                </>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })
                  )}
                </div>
              </div>

              {/* Scoped Project Audit History */}
              <div className="border-t border-slate-200 pt-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-slate-800">
                    Nhật ký kiểm toán dự án: <span className="font-bold">{selectedProject.name}</span>
                  </h3>
                  <span className="text-xs text-slate-400">Chỉ xem (Read-only)</span>
                </div>

                {auditAccessDenied ? (
                  <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4 text-center">
                    <p className="text-sm text-slate-500">
                      Không tìm thấy dự án hoặc không có quyền xem nhật ký kiểm toán (Fail-closed).
                    </p>
                  </div>
                ) : (
                  <div className="mt-4 space-y-2">
                    {auditEvents.length === 0 ? (
                      <p className="text-sm text-slate-400">Chưa có sự kiện kiểm toán nào.</p>
                    ) : (
                      auditEvents.map((ae) => (
                        <div
                          key={ae.id}
                          className="rounded border border-slate-200 bg-slate-50/50 p-3 text-xs text-slate-700"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-1 font-mono">
                            <span className="font-bold text-slate-900">{ae.action}</span>
                            <span className="text-slate-400">{ae.created_at}</span>
                          </div>
                          <div className="mt-1.5 grid grid-cols-1 gap-1 text-slate-600 sm:grid-cols-2">
                            <div>
                              <span className="font-medium text-slate-500">Người thực hiện: </span>
                              {ae.actor_id}
                            </div>
                            <div>
                              <span className="font-medium text-slate-500">Đối tượng: </span>
                              {ae.target_type} ({ae.target_id})
                            </div>
                            <div className="sm:col-span-2">
                              <span className="font-medium text-slate-500">Correlation ID: </span>
                              {ae.correlation_id}
                            </div>
                          </div>
                          {(ae.before_values || ae.after_values) && (
                            <div className="mt-2 rounded bg-white p-2 border border-slate-200 font-mono text-[11px]">
                              {ae.before_values && (
                                <div>
                                  <span className="text-slate-400">Trước: </span>
                                  {JSON.stringify(ae.before_values)}
                                </div>
                              )}
                              {ae.after_values && (
                                <div>
                                  <span className="text-slate-400">Sau: </span>
                                  {JSON.stringify(ae.after_values)}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))
                    )}

                    {hasMoreAudit && (
                      <div className="pt-2 text-center">
                        <button
                          
                          
                          onClick={handleLoadMoreAudit}
                          className="text-xs"
                        >
                          Tải thêm nhật ký kiểm toán
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  )
}
