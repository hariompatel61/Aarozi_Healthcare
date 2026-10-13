"""Authentication router for local login, session verification, and logout."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Header, Request, status, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.identity import User
from app.security.auth import (
    authenticate_user,
    get_current_user,
    revoke_session,
)
from app.security.tenant_guard import TenantContext, get_tenant_context

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    tenant_id_or_code: str = Field(..., description="Tenant ID or unique code (e.g. ACME)")
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user_id: str
    username: str
    full_name: str | None = None
    tenant_id: str
    is_superuser: bool


class UserSessionResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str | None = None
    tenant_id: str
    is_superuser: bool
    is_active: bool


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and create secure local session."""
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    auth_result = authenticate_user(
        db,
        tenant_id_or_code=payload.tenant_id_or_code,
        username=payload.username,
        password=payload.password,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant, username, or password",
        )

    user, session_rec = auth_result

    return LoginResponse(
        access_token=session_rec.session_token,
        token_type="bearer",
        expires_at=session_rec.expires_at.isoformat(),
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        tenant_id=user.tenant_id,
        is_superuser=user.is_superuser,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Revoke current session and logout."""
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            revoke_session(db, parts[1], actor_user_id=current_user.id)

    return {"status": "logged_out"}


@router.get("/session", response_model=UserSessionResponse, status_code=status.HTTP_200_OK)
def get_session(
    current_user: User = Depends(get_current_user),
    tenant_context: TenantContext | None = Depends(get_tenant_context),
) -> UserSessionResponse:
    """Get current authenticated user session profile."""
    return UserSessionResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        tenant_id=current_user.tenant_id,
        is_superuser=current_user.is_superuser,
        is_active=current_user.is_active,
    )

