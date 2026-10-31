from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectLifecycle(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ProjectRole(StrEnum):
    PROJECT_MANAGER = "project_manager"
    MEMBER = "member"
    AUDITOR = "auditor"


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)
    lead_department_id: str | None = Field(default=None, max_length=36)
    start_date: date | None = None
    end_date: date | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    lead_department_id: str | None = None
    project_manager_id: str
    start_date: date | None = None
    end_date: date | None = None
    lifecycle: str
    created_at: datetime
    updated_at: datetime


class ProjectMemberAssign(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=36)
    role: ProjectRole


class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    user_id: str
    role: str
    assigned_by: str
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    assignee_id: str | None = Field(default=None, max_length=36)
    due_date: datetime | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    description: str | None = None
    creator_id: str
    assignee_id: str | None = None
    due_date: datetime | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskStatusCounts(BaseModel):
    open: int = 0
    in_progress: int = 0
    blocked: int = 0
    done: int = 0
    cancelled: int = 0


class ProjectDashboardItem(BaseModel):
    project_id: str
    project_name: str
    lifecycle: str
    task_status_counts: TaskStatusCounts
    overdue_task_count: int
    total_task_count: int


class DashboardSummaryResponse(BaseModel):
    projects: list[ProjectDashboardItem]
    total_projects: int
    total_tasks: int
    total_overdue_tasks: int
    total_task_status_counts: TaskStatusCounts


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    action: str
    target_type: str
    target_id: str
    project_id: str
    correlation_id: str
    created_at: datetime
    before_values: dict[str, Any] | None = None
    after_values: dict[str, Any] | None = None


class AuditEventListResponse(BaseModel):
    items: list[AuditEventRead]
    next_cursor: str | None = None
    has_more: bool = False
