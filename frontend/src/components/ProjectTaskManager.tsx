import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'

export interface ProjectItem {
  id: string
  name: string
  description?: string | null
  lifecycle: string
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
  status: 'open' | 'in_progress' | 'blocked' | 'done' | 'cancelled'
  due_date?: string | null
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

export function ProjectTaskManager() {
  const [projects, setProjects] = useState<ProjectItem[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummaryResponse | null>(null)
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [auditEvents, setAuditEvents] = useState<AuditEventItem[]>([])
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [hasMoreAudit, setHasMoreAudit] = useState<boolean>(false)
  const [auditAccessDenied, setAuditAccessDenied] = useState<boolean>(false)
  const [authError, setAuthError] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // Fetch authorized projects and dashboard summary from server using session cookie
  useEffect(() => {
    let ignore = false
    async function loadInitialData() {
      try {
        const [projRes, dashRes] = await Promise.all([
          fetch('/api/v1/projects', { credentials: 'include' }),
          fetch('/api/v1/dashboard/summary', { credentials: 'include' }),
        ])

        if (ignore) return

        if (projRes.status === 401 || dashRes.status === 401) {
          setAuthError('Yêu cầu phiên đăng nhập hợp lệ để truy cập dữ liệu dự án.')
          setLoading(false)
          return
        }

        if (projRes.ok) {
          const projData: ProjectItem[] = await projRes.json()
          if (!ignore) {
            setProjects(projData)
            if (projData.length > 0) {
              setSelectedProjectId((prev) => prev ?? projData[0].id)
            }
          }
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

    void loadInitialData()
    return () => {
      ignore = true
    }
  }, [])

  // Fetch tasks and audit history for selected project
  useEffect(() => {
    if (!selectedProjectId) return
    let ignore = false

    async function loadProjectDetails() {
      try {
        const [tasksRes, auditRes] = await Promise.all([
          fetch(`/api/v1/projects/${selectedProjectId}/tasks`, { credentials: 'include' }),
          fetch(`/api/v1/projects/${selectedProjectId}/audit-events?limit=20`, { credentials: 'include' }),
        ])

        if (ignore) return

        if (tasksRes.ok) {
          const tasksData: TaskItem[] = await tasksRes.json()
          if (!ignore) setTasks(tasksData)
        } else {
          if (!ignore) setTasks([])
        }

        if (auditRes.ok) {
          const auditData: AuditEventListResponse = await auditRes.json()
          if (!ignore) {
            setAuditEvents(auditData.items)
            setNextCursor(auditData.next_cursor)
            setHasMoreAudit(auditData.has_more)
            setAuditAccessDenied(false)
          }
        } else {
          if (!ignore) {
            setAuditEvents([])
            setNextCursor(null)
            setHasMoreAudit(false)
            setAuditAccessDenied(true)
          }
        }
      } catch {
        if (!ignore) {
          setTasks([])
          setAuditEvents([])
          setAuditAccessDenied(true)
        }
      }
    }

    void loadProjectDetails()
    return () => {
      ignore = true
    }
  }, [selectedProjectId])

  // Load more audit events using bounded cursor pagination
  const handleLoadMoreAudit = async () => {
    if (!selectedProjectId || !nextCursor) return
    try {
      const auditRes = await fetch(
        `/api/v1/projects/${selectedProjectId}/audit-events?limit=20&cursor=${encodeURIComponent(nextCursor)}`,
        { credentials: 'include' }
      )
      if (auditRes.ok) {
        const auditData: AuditEventListResponse = await auditRes.json()
        setAuditEvents((prev) => [...prev, ...auditData.items])
        setNextCursor(auditData.next_cursor)
        setHasMoreAudit(auditData.has_more)
      }
    } catch {
      // Gracefully handle network/pagination error
    }
  }

  const selectedProject = projects.find((p) => p.id === selectedProjectId)
  const selectedDashboard = dashboardSummary?.projects.find((p) => p.project_id === selectedProjectId)

  return (
    <section className="mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Quản lý Dự án & Bảng điều khiển Scoped (CHPMIS-005)
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Tổng quan công việc theo dự án và truy vết nhật ký kiểm toán bảo vệ bằng phiên máy chủ.
          </p>
        </div>
        <div className="text-xs text-slate-500">
          Xác thực: <span className="font-semibold text-slate-700">Phiên HTTP-only Cookie</span>
        </div>
      </div>

      {authError && (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800" role="alert">
          {authError}
        </div>
      )}

      {loading && !authError && (
        <p className="mt-4 text-sm text-slate-400">Đang tải dữ liệu từ máy chủ...</p>
      )}

      {/* Projects List */}
      <div className="mt-6">
        <h3 className="text-sm font-semibold text-slate-700">Danh sách dự án được phân công</h3>
        {projects.length === 0 ? (
          <p className="mt-2 text-sm text-slate-400">
            {loading ? 'Đang kiểm tra...' : 'Bạn chưa được phân công vào dự án nào.'}
          </p>
        ) : (
          <div className="mt-2 flex flex-wrap gap-2">
            {projects.map((proj) => (
              <button
                key={proj.id}
                onClick={() => setSelectedProjectId(proj.id)}
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

      {/* Scoped Dashboard Summary */}
      {selectedProject && (
        <div className="mt-6 rounded-md bg-slate-50 p-4 border border-slate-200">
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
      )}

      {/* Selected Project Tasks List */}
      {selectedProject && (
        <div className="mt-6 border-t border-slate-100 pt-6">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800">
              Danh sách công việc: <span className="font-bold">{selectedProject.name}</span>
            </h3>
            <span className="rounded bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
              {selectedProject.lifecycle}
            </span>
          </div>

          <div className="mt-4 space-y-2">
            {tasks.length === 0 ? (
              <p className="text-sm text-slate-400">Chưa có công việc nào trong dự án này.</p>
            ) : (
              tasks.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between rounded-md border border-slate-200 p-3"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">{t.title}</p>
                    <div className="mt-1 flex items-center gap-2">
                      <span className="inline-block rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                        {t.status}
                      </span>
                      {t.due_date && (
                        <span className="text-xs text-slate-500">
                          Hạn: {new Date(t.due_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Scoped Project Audit History View */}
      {selectedProject && (
        <div className="mt-8 border-t border-slate-200 pt-6">
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
                <div className="mt-3 text-center">
                  <Button
                    type="button"
                    onClick={() => {
                      void handleLoadMoreAudit()
                    }}
                    className="text-xs"
                  >
                    Xem thêm sự kiện kiểm toán
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
