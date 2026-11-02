from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.auth.models import SystemAdminRequest, User, UserRole, utc_now
from app.auth.oidc import (
    OIDC_BINDING_COOKIE_NAME,
    initiate_login_transaction,
    process_callback,
)
from app.auth.policy import (
    Role,
)
from app.auth.session import (
    revoke_session,
    revoke_user_sessions,
    validate_csrf,
    validate_session,
)
from app.config import Settings
from app.database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_settings(request: Request) -> Settings:
    return getattr(request.app.state, "settings", None) or Settings()


class SystemAdminRoleChangeRequest(BaseModel):
    target_user_id: str


class SystemAdminApprovalRequest(BaseModel):
    request_id: str


@router.get("/login")
def login(
    request: Request,
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    auth_url, binding_cookie = initiate_login_transaction(db, settings)
    response = RedirectResponse(url=auth_url, status_code=303)
    response.set_cookie(
        key=OIDC_BINDING_COOKIE_NAME,
        value=binding_cookie,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=600,
        path="/",
    )
    return response


@router.get("/callback")
def callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    oidc_client = getattr(request.app.state, "oidc_client", None)
    key_resolver = getattr(request.app.state, "key_resolver", None)
    binding_cookie = request.cookies.get(OIDC_BINDING_COOKIE_NAME)

    consumed = False

    def mark_consumed() -> None:
        nonlocal consumed
        consumed = True

    try:
        user, session = process_callback(
            db,
            settings,
            code,
            state,
            browser_binding_cookie=binding_cookie,
            oidc_client=oidc_client,
            key_resolver=key_resolver,
            on_consumed=mark_consumed,
        )
    except HTTPException as exc:
        if consumed:
            response = JSONResponse(
                {"detail": exc.detail},
                status_code=exc.status_code,
                headers=dict(exc.headers) if exc.headers else None,
            )
            response.delete_cookie(
                key=OIDC_BINDING_COOKIE_NAME,
                path="/",
                httponly=True,
                secure=settings.session_cookie_secure,
                samesite="lax",
            )
            return response
        raise
    except Exception:
        if consumed:
            response = JSONResponse(
                {"detail": "Authentication failed"},
                status_code=500,
            )
            response.delete_cookie(
                key=OIDC_BINDING_COOKIE_NAME,
                path="/",
                httponly=True,
                secure=settings.session_cookie_secure,
                samesite="lax",
            )
            return response
        raise

    response = JSONResponse(
        {
            "status": "authenticated",
            "user": {
                "id": user.id,
                "sub": user.sub,
                "email": user.email,
                "name": user.name,
                "department": user.department,
            },
        }
    )

    # Clear browser-binding cookie after consumption
    response.delete_cookie(
        key=OIDC_BINDING_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )

    # Set Secure, HttpOnly, SameSite=Lax cookie for opaque session
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session.id,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    # Set CSRF cookie (readable by JS to populate X-CSRF-Token header)
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=session.csrf_token,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    return response


@router.get("/session")
def get_current_session(
    pmis_session: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    if not pmis_session:
        raise HTTPException(status_code=401, detail="Missing session cookie")

    session, user, roles = validate_session(db, pmis_session, settings)
    return JSONResponse(
        {
            "user": {
                "id": user.id,
                "sub": user.sub,
                "email": user.email,
                "name": user.name,
                "department": user.department,
            },
            "roles": roles,
            "csrf_token": session.csrf_token,
        }
    )


@router.delete("/session")
def logout(
    request: Request,
    pmis_session: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    if not pmis_session:
        raise HTTPException(status_code=401, detail="Missing session cookie")

    session, user, roles = validate_session(db, pmis_session, settings)
    validate_csrf(session, x_csrf_token)

    revoke_session(db, session.id)

    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    response.delete_cookie(key=settings.csrf_cookie_name, path="/")
    return response


@router.post("/roles/system-admin/grant")
def request_grant_system_admin_role(
    payload: SystemAdminRoleChangeRequest,
    pmis_session: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    if not pmis_session:
        raise HTTPException(status_code=401, detail="Missing session cookie")

    session, actor_user, actor_roles = validate_session(db, pmis_session, settings)
    validate_csrf(session, x_csrf_token)

    if Role.SYSTEM_ADMIN not in actor_roles:
        raise HTTPException(status_code=403, detail="Actor must be an active System Admin")

    if payload.target_user_id == actor_user.id:
        raise HTTPException(status_code=403, detail="System Admin cannot self-grant")

    target_user = db.query(User).filter_by(id=payload.target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    existing_grant = (
        db.query(UserRole).filter_by(user_id=payload.target_user_id, role=Role.SYSTEM_ADMIN).first()
    )
    if existing_grant:
        raise HTTPException(status_code=400, detail="Target user already has System Admin role")

    req = SystemAdminRequest(
        target_user_id=payload.target_user_id,
        action="grant",
        status="pending",
        requester_id=actor_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    return JSONResponse(
        {
            "status": "pending_approval",
            "request_id": req.id,
            "target_user_id": payload.target_user_id,
            "action": "grant",
        },
        status_code=202,
    )


@router.post("/roles/system-admin/revoke")
def request_revoke_system_admin_role(
    payload: SystemAdminRoleChangeRequest,
    pmis_session: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    if not pmis_session:
        raise HTTPException(status_code=401, detail="Missing session cookie")

    session, actor_user, actor_roles = validate_session(db, pmis_session, settings)
    validate_csrf(session, x_csrf_token)

    if Role.SYSTEM_ADMIN not in actor_roles:
        raise HTTPException(status_code=403, detail="Actor must be an active System Admin")

    target_user = db.query(User).filter_by(id=payload.target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    existing_grant = (
        db.query(UserRole).filter_by(user_id=payload.target_user_id, role=Role.SYSTEM_ADMIN).first()
    )
    if not existing_grant:
        raise HTTPException(status_code=400, detail="Target user does not have System Admin role")

    req = SystemAdminRequest(
        target_user_id=payload.target_user_id,
        action="revoke",
        status="pending",
        requester_id=actor_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    return JSONResponse(
        {
            "status": "pending_approval",
            "request_id": req.id,
            "target_user_id": payload.target_user_id,
            "action": "revoke",
        },
        status_code=202,
    )


@router.post("/roles/system-admin/approve")
def approve_system_admin_role_request(
    payload: SystemAdminApprovalRequest,
    pmis_session: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    if not pmis_session:
        raise HTTPException(status_code=401, detail="Missing session cookie")

    session, actor_user, actor_roles = validate_session(db, pmis_session, settings)
    validate_csrf(session, x_csrf_token)

    if Role.SYSTEM_ADMIN not in actor_roles:
        raise HTTPException(status_code=403, detail="Approver must be an active System Admin")

    try:
        req = (
            db.query(SystemAdminRequest).filter_by(id=payload.request_id).with_for_update().first()
        )
        if not req:
            raise HTTPException(status_code=404, detail="System Admin request not found")

        if req.status != "pending":
            raise HTTPException(
                status_code=409, detail=f"Request is already decided ({req.status})"
            )

        # Dual control: Requester and approver must be distinct existing system admins
        if req.requester_id == actor_user.id:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Requester cannot approve own request; distinct second System Admin required"
                ),
            )

        # Self-grant prevention for approver
        if req.action == "grant" and req.target_user_id == actor_user.id:
            raise HTTPException(status_code=403, detail="System Admin cannot self-grant")

        # Revalidate approver within decision transaction
        approver = db.query(User).filter_by(id=actor_user.id).populate_existing().first()
        if not approver or not approver.is_active:
            raise HTTPException(
                status_code=403, detail="Approver account is inactive or deprovisioned"
            )

        approver_role = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == actor_user.id,
                UserRole.role == Role.SYSTEM_ADMIN.value,
            )
            .populate_existing()
            .first()
        )
        if not approver_role:
            raise HTTPException(status_code=403, detail="Approver must be an active System Admin")

        # Revalidate requester within decision transaction
        requester = db.query(User).filter_by(id=req.requester_id).first()
        if not requester or not requester.is_active:
            raise HTTPException(
                status_code=403, detail="Requester account is inactive or deprovisioned"
            )

        requester_role = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == req.requester_id,
                UserRole.role == Role.SYSTEM_ADMIN.value,
            )
            .first()
        )
        if not requester_role:
            raise HTTPException(
                status_code=403, detail="Requester is no longer an active System Admin"
            )

        # Revalidate target user existence
        target_user = db.query(User).filter_by(id=req.target_user_id).with_for_update().first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")

        # Revalidate action preconditions and apply privilege change
        existing_grant = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == req.target_user_id,
                UserRole.role.in_([Role.SYSTEM_ADMIN.value, "System Admin"]),
            )
            .first()
        )

        if req.action == "grant":
            if existing_grant:
                raise HTTPException(
                    status_code=409,
                    detail="Target user already has System Admin role",
                )
            grant_record = UserRole(
                user_id=req.target_user_id,
                role=Role.SYSTEM_ADMIN.value,
                granted_by=req.requester_id,
                second_admin_id=actor_user.id,
            )
            db.add(grant_record)
            revoke_user_sessions(db, req.target_user_id)
        elif req.action == "revoke":
            if not existing_grant:
                raise HTTPException(
                    status_code=409,
                    detail="Target user does not have System Admin role to revoke",
                )
            db.delete(existing_grant)
            revoke_user_sessions(db, req.target_user_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported request action: {req.action}")

        # Durable audit record update
        req.status = "approved"
        req.approver_id = actor_user.id
        req.decided_at = utc_now()
        db.commit()

        return JSONResponse(
            {
                "status": "approved",
                "request_id": req.id,
                "target_user_id": req.target_user_id,
                "action": req.action,
                "role": Role.SYSTEM_ADMIN,
            }
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to process approval decision",
        ) from None


@router.get("/roles/system-admin/requests")
def list_system_admin_requests(
    pmis_session: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    if not pmis_session:
        raise HTTPException(status_code=401, detail="Missing session cookie")
    session, actor_user, actor_roles = validate_session(db, pmis_session, settings)
    if Role.SYSTEM_ADMIN not in actor_roles:
        raise HTTPException(status_code=403, detail="Forbidden")

    requests = db.query(SystemAdminRequest).order_by(SystemAdminRequest.created_at.desc()).all()
    return JSONResponse(
        {
            "requests": [
                {
                    "id": r.id,
                    "target_user_id": r.target_user_id,
                    "action": r.action,
                    "status": r.status,
                    "requester_id": r.requester_id,
                    "approver_id": r.approver_id,
                    "created_at": r.created_at.isoformat(),
                    "decided_at": r.decided_at.isoformat() if r.decided_at else None,
                }
                for r in requests
            ]
        }
    )
