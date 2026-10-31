import uuid

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session as DBSession

from app.auth.models import User
from app.auth.policy import Role
from app.auth.session import validate_session
from app.config import Settings
from app.database import get_db
from app.projects.models import Project, ProjectMember, Task
from app.projects.schemas import (
    AuditEventListResponse,
    DashboardSummaryResponse,
    ProjectCreate,
    ProjectMemberAssign,
    ProjectMemberRead,
    ProjectRead,
    TaskCreate,
    TaskRead,
    TaskStatusUpdate,
)
from app.projects.service import (
    archive_project,
    assign_project_member,
    create_project,
    create_task,
    get_dashboard_summary,
    get_user_project_role,
    list_project_audit_events,
    transition_task_status,
)

router = APIRouter(prefix="/api/v1", tags=["projects-tasks"])


def get_settings(request: Request) -> Settings:
    return getattr(request.app.state, "settings", None) or Settings()


def get_current_user_and_roles(
    pmis_session: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> tuple[User, list[str], str]:
    if not pmis_session:
        raise HTTPException(status_code=401, detail="Authentication required")
    session, user, roles = validate_session(db, pmis_session, settings)
    return user, roles, session.csrf_token


def get_correlation_id(
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
) -> str:
    return x_correlation_id or str(uuid.uuid4())


# ============================================================================
# Project Routes
# ============================================================================


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    db: DBSession = Depends(get_db),
) -> list[Project]:
    user, _, _ = auth_data
    # Deny by default: return only projects where the caller is explicitly an assigned member
    assigned_project_ids = db.query(ProjectMember.project_id).filter_by(user_id=user.id).all()
    p_ids = [p[0] for p in assigned_project_ids]
    if not p_ids:
        return []
    return db.query(Project).filter(Project.id.in_(p_ids)).all()


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_new_project(
    payload: ProjectCreate,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    correlation_id: str = Depends(get_correlation_id),
    db: DBSession = Depends(get_db),
) -> Project:
    user, roles, csrf_token = auth_data
    if not x_csrf_token or x_csrf_token != csrf_token:
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")

    # Project creation is initiated by an authenticated Project Manager
    if Role.PROJECT_MANAGER.value not in roles:
        raise HTTPException(status_code=403, detail="Only Project Managers can create projects")

    return create_project(
        db=db,
        actor_id=user.id,
        payload=payload,
        correlation_id=correlation_id,
    )


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project_details(
    project_id: str,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    db: DBSession = Depends(get_db),
) -> Project:
    user, _, _ = auth_data
    # Inaccessible records must not disclose existence
    role = get_user_project_role(db, user.id, project_id)
    if not role:
        raise HTTPException(status_code=404, detail="Project not found")

    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects/{project_id}/archive", response_model=ProjectRead)
def archive_existing_project(
    project_id: str,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    correlation_id: str = Depends(get_correlation_id),
    db: DBSession = Depends(get_db),
) -> Project:
    user, _, csrf_token = auth_data
    if not x_csrf_token or x_csrf_token != csrf_token:
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")

    return archive_project(
        db=db,
        actor_id=user.id,
        project_id=project_id,
        correlation_id=correlation_id,
    )


# ============================================================================
# Project Membership Routes
# ============================================================================


@router.post("/projects/{project_id}/members", response_model=ProjectMemberRead)
@router.post("/projects/{project_id}/assignments", response_model=ProjectMemberRead)
def assign_member(
    project_id: str,
    payload: ProjectMemberAssign,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    correlation_id: str = Depends(get_correlation_id),
    db: DBSession = Depends(get_db),
):
    from fastapi.encoders import jsonable_encoder
    from fastapi.responses import JSONResponse

    user, _, csrf_token = auth_data
    if not x_csrf_token or x_csrf_token != csrf_token:
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")

    member, created = assign_project_member(
        db=db,
        actor_id=user.id,
        project_id=project_id,
        payload=payload,
        correlation_id=correlation_id,
    )
    status_code = 201 if created else 200
    content = jsonable_encoder(ProjectMemberRead.model_validate(member))
    return JSONResponse(content=content, status_code=status_code)


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberRead])
def list_project_members(
    project_id: str,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    db: DBSession = Depends(get_db),
) -> list[ProjectMember]:
    user, _, _ = auth_data
    role = get_user_project_role(db, user.id, project_id)
    if not role:
        raise HTTPException(status_code=404, detail="Project not found")

    return db.query(ProjectMember).filter_by(project_id=project_id).all()


# ============================================================================
# Task Routes
# ============================================================================


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=201)
def create_project_task(
    project_id: str,
    payload: TaskCreate,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    correlation_id: str = Depends(get_correlation_id),
    db: DBSession = Depends(get_db),
) -> Task:
    user, _, csrf_token = auth_data
    if not x_csrf_token or x_csrf_token != csrf_token:
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")

    return create_task(
        db=db,
        actor_id=user.id,
        project_id=project_id,
        payload=payload,
        correlation_id=correlation_id,
    )


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
def list_project_tasks(
    project_id: str,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    db: DBSession = Depends(get_db),
) -> list[Task]:
    user, _, _ = auth_data
    role = get_user_project_role(db, user.id, project_id)
    if not role:
        raise HTTPException(status_code=404, detail="Project not found")

    return db.query(Task).filter_by(project_id=project_id).all()


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task_details(
    task_id: str,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    db: DBSession = Depends(get_db),
) -> Task:
    user, _, _ = auth_data
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    role = get_user_project_role(db, user.id, task.project_id)
    if not role:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.patch("/tasks/{task_id}/status", response_model=TaskRead)
def update_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    correlation_id: str = Depends(get_correlation_id),
    db: DBSession = Depends(get_db),
) -> Task:
    user, _, csrf_token = auth_data
    if not x_csrf_token or x_csrf_token != csrf_token:
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")

    return transition_task_status(
        db=db,
        actor_id=user.id,
        task_id=task_id,
        target_status=payload.status,
        correlation_id=correlation_id,
    )


# ============================================================================
# Dashboard Routes (CHPMIS-005)
# ============================================================================


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_scoped_dashboard_summary(
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    db: DBSession = Depends(get_db),
) -> DashboardSummaryResponse:
    user, _, _ = auth_data
    return get_dashboard_summary(db=db, user_id=user.id)


# ============================================================================
# Project Audit History Routes (CHPMIS-005)
# ============================================================================


@router.get("/projects/{project_id}/audit-events", response_model=AuditEventListResponse)
def get_project_audit_events(
    project_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
    auth_data: tuple[User, list[str], str] = Depends(get_current_user_and_roles),
    db: DBSession = Depends(get_db),
) -> AuditEventListResponse:
    user, _, _ = auth_data
    return list_project_audit_events(
        db=db,
        actor_id=user.id,
        project_id=project_id,
        limit=limit,
        cursor=cursor,
    )
