from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class Role(StrEnum):
    SYSTEM_ADMIN = "system_admin"
    PROJECT_MANAGER = "project_manager"
    MEMBER = "member"
    AUDITOR = "auditor"


class Action(StrEnum):
    # Role and user admin
    ROLE_GRANT = "role:grant"
    ROLE_REVOKE = "role:revoke"
    USER_MANAGE = "user:manage"
    USER_DEPROVISION = "user:deprovision"

    # Business data actions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_MANAGE = "project:manage"
    PROJECT_ASSIGN = "project:assign"
    PROJECT_ARCHIVE = "project:archive"

    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_MANAGE = "task:manage"
    TASK_TRANSITION = "task:transition"

    AUDIT_READ = "audit:read"


@dataclass
class Principal:
    id: str
    sub: str
    email: str
    name: str
    roles: list[str | Role] = field(default_factory=list)
    department: str | None = None
    is_active: bool = True


@dataclass
class ResourceContext:
    project_id: str | None = None
    task_id: str | None = None
    department: str | None = None
    project_role: str | None = None


class ProjectScopeResolver(Protocol):
    """Abstract interface for resolving project scope without coupling to project schema."""

    def get_project_for_task(self, task_id: str) -> str | None:
        """Resolve parent project ID for a task."""
        ...

    def is_user_assigned_to_project(
        self, user_id: str, project_id: str, required_role: str | None = None
    ) -> bool:
        """Check if user has an explicit assignment to the project."""
        ...

    def is_user_assigned_to_task(self, user_id: str, task_id: str) -> bool:
        """Check if user is assigned to the specific task."""
        ...

    def get_user_project_role(self, user_id: str, project_id: str) -> str | None:
        """Resolve user's role on the project if assigned."""
        ...


class DefaultProjectScopeResolver:
    """Default resolver that denies all project-level and task-level lookups."""

    def get_project_for_task(self, task_id: str) -> str | None:
        return None

    def is_user_assigned_to_project(
        self, user_id: str, project_id: str, required_role: str | None = None
    ) -> bool:
        return False

    def is_user_assigned_to_task(self, user_id: str, task_id: str) -> bool:
        return False

    def get_user_project_role(self, user_id: str, project_id: str) -> str | None:
        return None


class AuthorizationError(Exception):
    """Raised when an authorization check fails."""

    pass


def _is_role_permitted(
    role: str,
    act: str,
    principal: Principal,
    project_id: str | None,
    task_id: str | None,
    is_assigned_to_project: bool,
    res: ProjectScopeResolver,
) -> bool:
    if role == Role.SYSTEM_ADMIN.value:
        return act in (
            Action.ROLE_GRANT,
            Action.ROLE_REVOKE,
            Action.USER_MANAGE,
            Action.USER_DEPROVISION,
        )
    if role == Role.PROJECT_MANAGER.value:
        if act == Action.PROJECT_CREATE:
            return True
        if is_assigned_to_project:
            return act in (
                Action.PROJECT_READ,
                Action.PROJECT_MANAGE,
                Action.PROJECT_ASSIGN,
                Action.PROJECT_ARCHIVE,
                Action.TASK_CREATE,
                Action.TASK_READ,
                Action.TASK_MANAGE,
                Action.TASK_TRANSITION,
                Action.AUDIT_READ,
            )
        return False
    if role == Role.MEMBER.value:
        if is_assigned_to_project:
            if act in (Action.PROJECT_READ, Action.TASK_READ):
                return True
            if act == Action.TASK_UPDATE and task_id is not None:
                return res.is_user_assigned_to_task(principal.id, task_id)
        return False
    if role == Role.AUDITOR.value:
        if is_assigned_to_project and act == Action.AUDIT_READ:
            return True
        return False
    return False


def authorize(
    principal: Principal,
    action: str | Action,
    context: ResourceContext | None = None,
    resolver: ProjectScopeResolver | None = None,
) -> bool:
    """Enforce approved deny-by-default role and explicit project-scope authorization policy.

    Follows the owner-selected intersection rule (2026-11-01):
    allow an action only when every applicable role permits it.
    For project-scoped endpoints, the action must also be allowed by the user's
    ProjectMember.role for that project, the user must be explicitly assigned,
    and task-specific rules still apply.
    """
    if not principal.is_active or not principal.roles:
        return False

    res = resolver or DefaultProjectScopeResolver()
    roles = [str(r.value if isinstance(r, Role) else r) for r in principal.roles]
    act = str(action.value if isinstance(action, Action) else action)

    # Resolve effective project_id and task_id
    project_id = context.project_id if context else None
    task_id = context.task_id if context else None

    if task_id is not None:
        task_project_id = res.get_project_for_task(task_id)
        if task_project_id is None:
            return False
        if project_id is not None and project_id != task_project_id:
            return False
        project_id = task_project_id

    # Department membership alone grants no project access
    # Explicit project assignment is strictly required for project-scoped actions
    is_assigned_to_project = False
    project_role = getattr(context, "project_role", None) if context else None
    if project_id is not None:
        is_assigned_to_project = res.is_user_assigned_to_project(principal.id, project_id)
        if project_role is None and hasattr(res, "get_user_project_role"):
            project_role = res.get_user_project_role(principal.id, project_id)

    # 1. Global roles intersection: EVERY applicable role must permit the action
    for r in roles:
        if not _is_role_permitted(
            r, act, principal, project_id, task_id, is_assigned_to_project, res
        ):
            return False

    # 2. For project-scoped actions (where project_id is resolved):
    # The action must also be allowed by the user's ProjectMember.role for that project.
    if project_id is not None:
        if not is_assigned_to_project or project_role is None:
            return False
        proj_role_str = str(project_role.value if isinstance(project_role, Role) else project_role)
        if not _is_role_permitted(
            proj_role_str, act, principal, project_id, task_id, is_assigned_to_project, res
        ):
            return False

    return True


def grant_system_admin(
    actor: Principal,
    target_user_id: str,
    second_admin: Principal | None,
    existing_admin_ids: set[str],
) -> bool:
    """Dual-control requirement for granting System Admin role."""
    actor_roles = {str(r) for r in actor.roles}
    if Role.SYSTEM_ADMIN not in actor_roles or actor.id not in existing_admin_ids:
        raise AuthorizationError("Actor must be an existing active System Admin")

    if target_user_id == actor.id:
        raise AuthorizationError("System Admin cannot self-grant")

    if second_admin is None or second_admin.id == actor.id or second_admin.id == target_user_id:
        raise AuthorizationError(
            "Granting System Admin requires a distinct second existing System Admin"
        )

    second_admin_roles = {str(r) for r in second_admin.roles}
    if Role.SYSTEM_ADMIN not in second_admin_roles or second_admin.id not in existing_admin_ids:
        raise AuthorizationError("Second admin must be an active existing System Admin")

    return True


def revoke_system_admin(
    actor: Principal,
    target_user_id: str,
    second_admin: Principal | None,
    existing_admin_ids: set[str],
) -> bool:
    """Dual-control requirement for revoking System Admin role."""
    actor_roles = {str(r) for r in actor.roles}
    if Role.SYSTEM_ADMIN not in actor_roles or actor.id not in existing_admin_ids:
        raise AuthorizationError("Actor must be an existing active System Admin")

    if second_admin is None or second_admin.id == actor.id:
        raise AuthorizationError(
            "Revoking System Admin requires a distinct second existing System Admin"
        )

    second_admin_roles = {str(r) for r in second_admin.roles}
    if Role.SYSTEM_ADMIN not in second_admin_roles or second_admin.id not in existing_admin_ids:
        raise AuthorizationError("Second admin must be an active existing System Admin")

    return True
