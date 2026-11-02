import base64
import json
import uuid
from datetime import date, datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session as DBSession

from app.auth.models import User
from app.auth.policy import (
    Action,
    DefaultProjectScopeResolver,
    Principal,
    ProjectScopeResolver,
    ResourceContext,
    _is_role_permitted,
    authorize,
)
from app.projects.models import AuditEvent, Project, ProjectMember, Task, utc_now
from app.projects.schemas import (
    AuditEventListResponse,
    AuditEventRead,
    DashboardSummaryResponse,
    ProjectCreate,
    ProjectDashboardItem,
    ProjectMemberAssign,
    ProjectRole,
    TaskCreate,
    TaskStatus,
    TaskStatusCounts,
)

# Strict allowlist of auditable fields per target type
# Excludes free-form text: descriptions, names, titles, and secrets
AUDIT_ALLOWLIST: dict[str, set[str]] = {
    "project": {
        "lead_department_id",
        "project_manager_id",
        "start_date",
        "end_date",
        "lifecycle",
    },
    "project_member": {
        "project_id",
        "user_id",
        "role",
        "assigned_by",
    },
    "task": {
        "project_id",
        "creator_id",
        "assignee_id",
        "due_date",
        "status",
    },
}

ORDINARY_TRANSITIONS: dict[str, set[str]] = {
    TaskStatus.OPEN: {TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.BLOCKED, TaskStatus.DONE},
    TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS},
}

PM_ADDITIONAL_TRANSITIONS: dict[str, set[str]] = {
    TaskStatus.OPEN: {TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.CANCELLED},
    TaskStatus.BLOCKED: {TaskStatus.CANCELLED},
    TaskStatus.DONE: {TaskStatus.IN_PROGRESS},
}


def _filter_audit_values(target_type: str, values: dict[str, Any] | None) -> dict[str, Any] | None:
    if values is None:
        return None
    allowed_keys = AUDIT_ALLOWLIST.get(target_type, set())
    filtered = {}
    for k, v in values.items():
        if k in allowed_keys:
            if isinstance(v, (datetime, date)):
                filtered[k] = v.isoformat()
            else:
                filtered[k] = v
    return filtered


def record_audit_event(
    db: DBSession,
    actor_id: str,
    action: str,
    target_type: str,
    target_id: str,
    project_id: str,
    correlation_id: str,
    before_values: dict[str, Any] | None = None,
    after_values: dict[str, Any] | None = None,
) -> AuditEvent:
    """Record an audit event strictly enforcing field allowlists.

    Excludes description, freeform text, credentials, and tokens.
    Shares the active db transaction with business mutations.
    """
    clean_before = _filter_audit_values(target_type, before_values)
    clean_after = _filter_audit_values(target_type, after_values)

    event = AuditEvent(
        id=str(uuid.uuid4()),
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        project_id=project_id,
        correlation_id=correlation_id,
        before_values=clean_before,
        after_values=clean_after,
        created_at=utc_now(),
    )
    db.add(event)
    return event


class DatabaseProjectScopeResolver(ProjectScopeResolver):
    def __init__(self, db: DBSession):
        self.db = db

    def get_project_for_task(self, task_id: str) -> str | None:
        task = self.db.query(Task).filter_by(id=task_id).first()
        return task.project_id if task else None

    def is_user_assigned_to_project(
        self, user_id: str, project_id: str, required_role: str | None = None
    ) -> bool:
        query = self.db.query(ProjectMember).filter_by(user_id=user_id, project_id=project_id)
        if required_role is not None:
            query = query.filter_by(role=required_role)
        return query.first() is not None

    def is_user_assigned_to_task(self, user_id: str, task_id: str) -> bool:
        task = self.db.query(Task).filter_by(id=task_id, assignee_id=user_id).first()
        return task is not None

    def get_user_project_role(self, user_id: str, project_id: str) -> str | None:
        member = (
            self.db.query(ProjectMember).filter_by(user_id=user_id, project_id=project_id).first()
        )
        return member.role if member else None


def get_user_project_role(db: DBSession, user_id: str, project_id: str) -> str | None:
    member = db.query(ProjectMember).filter_by(user_id=user_id, project_id=project_id).first()
    return member.role if member else None


def create_project(
    db: DBSession,
    actor_id: str,
    payload: ProjectCreate,
    correlation_id: str,
) -> Project:
    project_id = str(uuid.uuid4())
    now = utc_now()
    project = Project(
        id=project_id,
        name=payload.name,
        description=payload.description,
        lead_department_id=payload.lead_department_id,
        project_manager_id=actor_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        lifecycle="active",
        created_at=now,
        updated_at=now,
    )
    db.add(project)

    # Initial PM automatically assigned as project member
    initial_member = ProjectMember(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=actor_id,
        role=ProjectRole.PROJECT_MANAGER.value,
        assigned_by=actor_id,
        created_at=now,
        updated_at=now,
    )
    db.add(initial_member)

    try:
        # Record audit event
        record_audit_event(
            db=db,
            actor_id=actor_id,
            action="project:create",
            target_type="project",
            target_id=project_id,
            project_id=project_id,
            correlation_id=correlation_id,
            before_values=None,
            after_values={
                "lead_department_id": project.lead_department_id,
                "project_manager_id": project.project_manager_id,
                "start_date": project.start_date,
                "end_date": project.end_date,
                "lifecycle": project.lifecycle,
            },
        )
        db.commit()
        db.refresh(project)
        return project
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed") from exc


def archive_project(
    db: DBSession,
    actor_id: str,
    project_id: str,
    correlation_id: str,
    actor_roles: list[str] | None = None,
) -> Project:
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    caller_role = get_user_project_role(db, actor_id, project_id)
    if not caller_role:
        raise HTTPException(status_code=404, detail="Project not found")
    if caller_role != ProjectRole.PROJECT_MANAGER.value:
        raise HTTPException(status_code=403, detail="Only Project Manager can archive a project")

    if actor_roles is not None:
        user = db.query(User).filter_by(id=actor_id).first()
        principal = Principal(
            id=actor_id,
            sub=user.sub if user else "",
            email=user.email if user else "",
            name=user.name if user else "",
            roles=actor_roles,
            is_active=user.is_active if user else True,
        )
        resolver = DatabaseProjectScopeResolver(db)
        if not authorize(
            principal,
            Action.PROJECT_ARCHIVE,
            ResourceContext(project_id=project_id, project_role=caller_role),
            resolver,
        ):
            raise HTTPException(
                status_code=403, detail="Only Project Manager can archive a project"
            )

    if project.lifecycle == "archived":
        return project

    old_lifecycle = project.lifecycle
    project.lifecycle = "archived"
    project.updated_at = utc_now()

    try:
        record_audit_event(
            db=db,
            actor_id=actor_id,
            action="project:archive",
            target_type="project",
            target_id=project_id,
            project_id=project_id,
            correlation_id=correlation_id,
            before_values={"lifecycle": old_lifecycle},
            after_values={"lifecycle": "archived"},
        )
        db.commit()
        db.refresh(project)
        return project
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed") from exc


def assign_project_member(
    db: DBSession,
    actor_id: str,
    project_id: str,
    payload: ProjectMemberAssign,
    correlation_id: str,
    actor_roles: list[str] | None = None,
) -> tuple[ProjectMember, bool]:
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    caller_role = get_user_project_role(db, actor_id, project_id)
    if not caller_role:
        raise HTTPException(status_code=404, detail="Project not found")
    if caller_role != ProjectRole.PROJECT_MANAGER.value:
        raise HTTPException(status_code=403, detail="Only Project Manager can assign members")

    if actor_roles is not None:
        user = db.query(User).filter_by(id=actor_id).first()
        principal = Principal(
            id=actor_id,
            sub=user.sub if user else "",
            email=user.email if user else "",
            name=user.name if user else "",
            roles=actor_roles,
            is_active=user.is_active if user else True,
        )
        resolver = DatabaseProjectScopeResolver(db)
        if not authorize(
            principal,
            Action.PROJECT_ASSIGN,
            ResourceContext(project_id=project_id, project_role=caller_role),
            resolver,
        ):
            raise HTTPException(status_code=403, detail="Only Project Manager can assign members")

    if project.lifecycle == "archived":
        raise HTTPException(status_code=400, detail="Cannot modify members of an archived project")

    # Validate target user
    target_user = db.query(User).filter_by(id=payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    if not target_user.is_active:
        raise HTTPException(status_code=400, detail="Target user is inactive")

    # Check existing membership
    existing_member = (
        db.query(ProjectMember).filter_by(project_id=project_id, user_id=payload.user_id).first()
    )

    now = utc_now()
    if existing_member:
        # Reassignment
        old_role = existing_member.role
        existing_member.role = payload.role.value
        existing_member.assigned_by = actor_id
        existing_member.updated_at = now

        try:
            record_audit_event(
                db=db,
                actor_id=actor_id,
                action="project:member:reassign",
                target_type="project_member",
                target_id=existing_member.id,
                project_id=project_id,
                correlation_id=correlation_id,
                before_values={
                    "project_id": project_id,
                    "user_id": payload.user_id,
                    "role": old_role,
                },
                after_values={
                    "project_id": project_id,
                    "user_id": payload.user_id,
                    "role": payload.role.value,
                },
            )
            db.commit()
            db.refresh(existing_member)
            return existing_member, False
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail="Transaction failed") from exc
    else:
        # New assignment
        member_id = str(uuid.uuid4())
        member = ProjectMember(
            id=member_id,
            project_id=project_id,
            user_id=payload.user_id,
            role=payload.role.value,
            assigned_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        db.add(member)

        try:
            record_audit_event(
                db=db,
                actor_id=actor_id,
                action="project:member:assign",
                target_type="project_member",
                target_id=member_id,
                project_id=project_id,
                correlation_id=correlation_id,
                before_values=None,
                after_values={
                    "project_id": project_id,
                    "user_id": payload.user_id,
                    "role": payload.role.value,
                    "assigned_by": actor_id,
                },
            )
            db.commit()
            db.refresh(member)
            return member, True
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail="Transaction failed") from exc


def create_task(
    db: DBSession,
    actor_id: str,
    project_id: str,
    payload: TaskCreate,
    correlation_id: str,
    actor_roles: list[str] | None = None,
) -> Task:
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    caller_role = get_user_project_role(db, actor_id, project_id)
    if not caller_role:
        raise HTTPException(status_code=404, detail="Project not found")
    if caller_role != ProjectRole.PROJECT_MANAGER.value:
        raise HTTPException(status_code=403, detail="Only Project Manager can create tasks")

    if actor_roles is not None:
        user = db.query(User).filter_by(id=actor_id).first()
        principal = Principal(
            id=actor_id,
            sub=user.sub if user else "",
            email=user.email if user else "",
            name=user.name if user else "",
            roles=actor_roles,
            is_active=user.is_active if user else True,
        )
        resolver = DatabaseProjectScopeResolver(db)
        if not authorize(
            principal,
            Action.TASK_CREATE,
            ResourceContext(project_id=project_id, project_role=caller_role),
            resolver,
        ):
            raise HTTPException(status_code=403, detail="Only Project Manager can create tasks")

    if project.lifecycle == "archived":
        raise HTTPException(status_code=400, detail="Cannot create tasks in an archived project")

    # Validate assignee if provided
    if payload.assignee_id is not None:
        assignee_member = (
            db.query(ProjectMember)
            .filter_by(project_id=project_id, user_id=payload.assignee_id)
            .first()
        )
        if not assignee_member:
            raise HTTPException(
                status_code=400,
                detail="Assignee must be an active member of this project",
            )
        target_user = db.query(User).filter_by(id=payload.assignee_id).first()
        if not target_user or not target_user.is_active:
            raise HTTPException(status_code=400, detail="Assignee is inactive or not found")

    task_id = str(uuid.uuid4())
    now = utc_now()
    task = Task(
        id=task_id,
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        creator_id=actor_id,
        assignee_id=payload.assignee_id,
        due_date=payload.due_date,
        status=TaskStatus.OPEN.value,
        created_at=now,
        updated_at=now,
    )
    db.add(task)

    try:
        record_audit_event(
            db=db,
            actor_id=actor_id,
            action="task:create",
            target_type="task",
            target_id=task_id,
            project_id=project_id,
            correlation_id=correlation_id,
            before_values=None,
            after_values={
                "project_id": project_id,
                "creator_id": task.creator_id,
                "assignee_id": task.assignee_id,
                "due_date": task.due_date,
                "status": task.status,
            },
        )
        db.commit()
        db.refresh(task)
        return task
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed") from exc


def transition_task_status(
    db: DBSession,
    actor_id: str,
    task_id: str,
    target_status: TaskStatus,
    correlation_id: str,
    actor_roles: list[str] | None = None,
) -> Task:
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project = db.query(Project).filter_by(id=task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Task not found")

    caller_role = get_user_project_role(db, actor_id, task.project_id)
    if not caller_role:
        # Inaccessible record must not disclose existence
        raise HTTPException(status_code=404, detail="Task not found")

    if project.lifecycle == "archived":
        raise HTTPException(status_code=400, detail="Cannot modify tasks in an archived project")

    current_status = task.status
    target = target_status.value

    # Terminal state check
    if current_status == TaskStatus.CANCELLED.value:
        raise HTTPException(status_code=400, detail="Task is in terminal cancelled state")

    if caller_role == ProjectRole.AUDITOR.value:
        raise HTTPException(status_code=403, detail="Auditor cannot modify task status")

    if actor_roles is not None:
        user = db.query(User).filter_by(id=actor_id).first()
        principal = Principal(
            id=actor_id,
            sub=user.sub if user else "",
            email=user.email if user else "",
            name=user.name if user else "",
            roles=actor_roles,
            is_active=user.is_active if user else True,
        )
        resolver = DatabaseProjectScopeResolver(db)
        required_act = (
            Action.TASK_UPDATE
            if caller_role == ProjectRole.MEMBER.value
            else Action.TASK_TRANSITION
        )
        if not authorize(
            principal,
            required_act,
            ResourceContext(project_id=task.project_id, task_id=task_id, project_role=caller_role),
            resolver,
        ):
            raise HTTPException(status_code=403, detail="Unauthorized to transition task")

    if caller_role == ProjectRole.MEMBER.value:
        # Member can only transition own assigned task
        if task.assignee_id != actor_id:
            raise HTTPException(
                status_code=403, detail="Members may only transition tasks assigned to them"
            )

        # Member can only use ordinary work path
        is_reopen = (
            current_status == TaskStatus.DONE.value and target == TaskStatus.IN_PROGRESS.value
        )
        if target == TaskStatus.CANCELLED.value or is_reopen:
            raise HTTPException(
                status_code=403, detail="Only Project Manager can cancel or reopen tasks"
            )

        allowed_next = ORDINARY_TRANSITIONS.get(current_status, set())
        if target not in allowed_next:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transition from {current_status} to {target}",
            )

    elif caller_role == ProjectRole.PROJECT_MANAGER.value:
        allowed_next = ORDINARY_TRANSITIONS.get(
            current_status, set()
        ) | PM_ADDITIONAL_TRANSITIONS.get(current_status, set())
        if target not in allowed_next:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transition from {current_status} to {target}",
            )
    else:
        raise HTTPException(status_code=403, detail="Unauthorized to transition task")

    old_status = task.status
    task.status = target
    task.updated_at = utc_now()

    try:
        record_audit_event(
            db=db,
            actor_id=actor_id,
            action="task:transition",
            target_type="task",
            target_id=task_id,
            project_id=task.project_id,
            correlation_id=correlation_id,
            before_values={"status": old_status},
            after_values={"status": target},
        )
        db.commit()
        db.refresh(task)
        return task
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed") from exc


# ============================================================================
# Centralized Overdue & Dashboard Summary & Audit Read Services (CHPMIS-005)
# ============================================================================


def is_task_overdue(
    due_date: datetime | None,
    status: str,
    as_of: datetime | None = None,
) -> bool:
    """Centralized definition of overdue task.

    An overdue task is one with a non-null due date earlier than the current UTC
    instant and status other than terminal done or cancelled.
    """
    if due_date is None:
        return False
    if status in (TaskStatus.DONE.value, TaskStatus.CANCELLED.value):
        return False
    current_time = as_of or utc_now()
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    return due_date < current_time


def encode_audit_cursor(project_id: str, created_at: datetime, event_id: str) -> str:
    payload = {
        "project_id": project_id,
        "created_at": created_at.isoformat(),
        "id": event_id,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_audit_cursor(cursor: str, expected_project_id: str) -> dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid cursor")

    if "project_id" not in payload or "created_at" not in payload or "id" not in payload:
        raise HTTPException(status_code=400, detail="Invalid cursor")

    if payload["project_id"] != expected_project_id:
        raise HTTPException(status_code=400, detail="Invalid cursor for this project")

    try:
        created_at = datetime.fromisoformat(payload["created_at"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc

    return {
        "project_id": payload["project_id"],
        "created_at": created_at,
        "id": payload["id"],
    }


def get_dashboard_summary(
    db: DBSession,
    user_id: str,
    as_of: datetime | None = None,
    actor_roles: list[str] | None = None,
) -> DashboardSummaryResponse:
    empty_resp = DashboardSummaryResponse(
        projects=[],
        total_projects=0,
        total_tasks=0,
        total_overdue_tasks=0,
        total_task_status_counts=TaskStatusCounts(),
    )

    # Global role intersection: if any role denies business read, return empty summary
    if actor_roles is not None:
        if not actor_roles:
            return empty_resp
        user = db.query(User).filter_by(id=user_id).first()
        principal = Principal(
            id=user_id,
            sub=user.sub if user else "",
            email=user.email if user else "",
            name=user.name if user else "",
            roles=actor_roles,
            is_active=user.is_active if user else True,
        )
        for r in actor_roles:
            if not _is_role_permitted(
                r,
                Action.PROJECT_READ.value,
                principal,
                "dummy",
                None,
                True,
                DefaultProjectScopeResolver(),
            ):
                return empty_resp

    # Deny-by-default: resolve explicit project memberships for caller
    # Only include projects where user has read-permitted role (PM or Member, not Auditor)
    assigned_memberships = (
        db.query(ProjectMember.project_id)
        .filter(
            ProjectMember.user_id == user_id,
            ProjectMember.role.in_([ProjectRole.PROJECT_MANAGER.value, ProjectRole.MEMBER.value]),
        )
        .all()
    )
    assigned_project_ids = [m[0] for m in assigned_memberships]

    if not assigned_project_ids:
        return empty_resp

    projects = db.query(Project).filter(Project.id.in_(assigned_project_ids)).all()

    project_items: list[ProjectDashboardItem] = []
    total_open = 0
    total_in_progress = 0
    total_blocked = 0
    total_done = 0
    total_cancelled = 0
    total_overdue = 0
    total_tasks = 0

    current_time = as_of or utc_now()

    for project in projects:
        tasks = db.query(Task).filter_by(project_id=project.id).all()
        p_open = sum(1 for t in tasks if t.status == TaskStatus.OPEN.value)
        p_in_prog = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS.value)
        p_blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED.value)
        p_done = sum(1 for t in tasks if t.status == TaskStatus.DONE.value)
        p_cancelled = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED.value)
        p_overdue = sum(
            1 for t in tasks if is_task_overdue(t.due_date, t.status, as_of=current_time)
        )
        p_total = len(tasks)

        total_open += p_open
        total_in_progress += p_in_prog
        total_blocked += p_blocked
        total_done += p_done
        total_cancelled += p_cancelled
        total_overdue += p_overdue
        total_tasks += p_total

        project_items.append(
            ProjectDashboardItem(
                project_id=project.id,
                project_name=project.name,
                lifecycle=project.lifecycle,
                task_status_counts=TaskStatusCounts(
                    open=p_open,
                    in_progress=p_in_prog,
                    blocked=p_blocked,
                    done=p_done,
                    cancelled=p_cancelled,
                ),
                overdue_task_count=p_overdue,
                total_task_count=p_total,
            )
        )

    return DashboardSummaryResponse(
        projects=project_items,
        total_projects=len(project_items),
        total_tasks=total_tasks,
        total_overdue_tasks=total_overdue,
        total_task_status_counts=TaskStatusCounts(
            open=total_open,
            in_progress=total_in_progress,
            blocked=total_blocked,
            done=total_done,
            cancelled=total_cancelled,
        ),
    )


def list_project_audit_events(
    db: DBSession,
    actor_id: str,
    project_id: str,
    limit: int = 50,
    cursor: str | None = None,
    actor_roles: list[str] | None = None,
) -> AuditEventListResponse:
    # Cap limit to maximum 100
    if limit > 100:
        limit = 100

    # Role enforcement: must be in-scope Project Manager or Auditor
    caller_role = get_user_project_role(db, actor_id, project_id)
    if not caller_role or caller_role not in (
        ProjectRole.PROJECT_MANAGER.value,
        ProjectRole.AUDITOR.value,
    ):
        raise HTTPException(status_code=404, detail="Project not found")

    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Global roles intersection check for Action.AUDIT_READ:
    if actor_roles is not None:
        user = db.query(User).filter_by(id=actor_id).first()
        principal = Principal(
            id=actor_id,
            sub=user.sub if user else "",
            email=user.email if user else "",
            name=user.name if user else "",
            roles=actor_roles,
            is_active=user.is_active if user else True,
        )
        resolver = DatabaseProjectScopeResolver(db)
        if not authorize(
            principal,
            Action.AUDIT_READ,
            ResourceContext(project_id=project_id, project_role=caller_role),
            resolver,
        ):
            raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(AuditEvent).filter(AuditEvent.project_id == project_id)

    if cursor:
        cursor_data = decode_audit_cursor(cursor, expected_project_id=project_id)
        c_time = cursor_data["created_at"]
        c_id = cursor_data["id"]
        if c_time.tzinfo is None:
            c_time = c_time.replace(tzinfo=timezone.utc)
        query = query.filter(
            or_(
                AuditEvent.created_at < c_time,
                and_(AuditEvent.created_at == c_time, AuditEvent.id < c_id),
            )
        )

    # Stable newest-first ordering
    query = query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
    events = query.limit(limit + 1).all()

    has_more = len(events) > limit
    page_events = events[:limit]

    # Map to AuditEventRead with strict safe-field allowlist
    items: list[AuditEventRead] = []
    for ev in page_events:
        safe_before = _filter_audit_values(ev.target_type, ev.before_values)
        safe_after = _filter_audit_values(ev.target_type, ev.after_values)
        items.append(
            AuditEventRead(
                id=ev.id,
                actor_id=ev.actor_id,
                action=ev.action,
                target_type=ev.target_type,
                target_id=ev.target_id,
                project_id=ev.project_id,
                correlation_id=ev.correlation_id,
                created_at=ev.created_at,
                before_values=safe_before,
                after_values=safe_after,
            )
        )

    next_cursor = None
    if has_more and page_events:
        last_item = page_events[-1]
        next_cursor = encode_audit_cursor(project_id, last_item.created_at, last_item.id)

    return AuditEventListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
    )
