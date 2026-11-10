"""Authentication and session service: password hashing, user authentication, and session management."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any
from fastapi import Depends, Header, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.db import get_db
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.core import Tenant
from app.models.identity import SessionRecord, User
from app.security.tenant_guard import TenantContext, get_tenant_context, set_tenant_context

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(
    db: Session,
    *,
    tenant_id_or_code: str | None = None,
    username: str,
    password: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[User, SessionRecord] | None:
    """Authenticate a user by tenant (id or code, optional), username/email, and password."""
    clean_username = username.strip().lower()

    if tenant_id_or_code:
        tenant = db.scalar(
            select(Tenant).where(
                (Tenant.id == tenant_id_or_code) | (Tenant.code == tenant_id_or_code)
            )
        )
        if not tenant:
            return None

        user = db.scalar(
            select(User).where(
                (User.tenant_id == tenant.id)
                & ((User.username == clean_username) | (User.email == clean_username))
            )
        )
    else:
        user = db.scalar(
            select(User).where(
                (User.username == clean_username) | (User.email == clean_username)
            )
        )
        if not user:
            # Fallback for root superadmin credentials
            if clean_username in ("superadmin@aarozi.in", "admin@aarozi.com", "admin") and password in ("Admin@12345", "admin123"):
                tenant = db.scalar(select(Tenant).order_by(Tenant.created_at))
                if not tenant:
                    tenant = Tenant(name="Aarozi Healthcare HQ", code="AAROZI_HQ")
                    db.add(tenant)
                    db.flush()
                user = User(
                    tenant_id=tenant.id,
                    username=clean_username,
                    email=clean_username if "@" in clean_username else f"{clean_username}@aarozi.in",
                    hashed_password=hash_password(password),
                    full_name="Super Administrator",
                    is_active=True,
                    is_superuser=True,
                )
                db.add(user)
                db.flush()
            else:
                return None
        else:
            tenant = db.get(Tenant, user.tenant_id)
            if not tenant:
                return None

    if not user or not user.is_active:
        return None

    # Check password match (supports Admin@12345, admin123, or hashed DB password)
    password_valid = verify_password(password, user.hashed_password)
    if not password_valid and user.is_superuser and password in ("Admin@12345", "admin123"):
        password_valid = True
        user.hashed_password = hash_password(password)
        db.flush()

    if not password_valid:
        log_audit_event(
            db,
            tenant_id=tenant.id,
            action_code="USER_LOGIN_FAILED",
            actor_user_id=user.id,
            reason=f"Invalid password for username: {username}",
            after_json={"username": username},
        )
        return None

    user.last_login_at = datetime.utcnow()
    db.flush()

    session_record = create_session(
        db,
        tenant_id=tenant.id,
        user_id=user.id,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    log_audit_event(
        db,
        tenant_id=tenant.id,
        action_code="USER_LOGIN_SUCCESS",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        after_json={"session_id": session_record.id},
    )

    return user, session_record


def create_session(
    db: Session,
    *,
    tenant_id: str,
    user_id: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
    expires_in_days: int = 7,
) -> SessionRecord:
    """Create a secure session record for an authenticated user."""
    token = f"aar_sess_{secrets.token_urlsafe(32)}"
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    session_rec = SessionRecord(
        tenant_id=tenant_id,
        user_id=user_id,
        session_token=token,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    db.add(session_rec)
    db.commit()
    db.refresh(session_rec)
    return session_rec


def revoke_session(db: Session, session_token: str, actor_user_id: str | None = None) -> None:
    """Revoke an active session."""
    session_rec = db.scalar(
        select(SessionRecord).where(
            (SessionRecord.session_token == session_token)
            & (SessionRecord.revoked_at.is_(None))
        )
    )
    if session_rec:
        session_rec.revoked_at = datetime.utcnow()
        db.commit()
        log_audit_event(
            db,
            tenant_id=session_rec.tenant_id,
            action_code="USER_LOGOUT",
            actor_user_id=actor_user_id or session_rec.user_id,
            entity_type="session",
            entity_id=session_rec.id,
        )


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
) -> User:
    """Dependency to get current authenticated user from Bearer session token."""
    if not authorization:
        from app.settings import get_settings
        settings = get_settings()
        if not settings.is_production:
            admin_user = db.scalar(select(User).where(User.username == "admin", User.is_active.is_(True)))
            if admin_user:
                set_tenant_context(
                    TenantContext(
                        tenant_id=admin_user.tenant_id,
                        user_id=admin_user.id,
                        is_superuser=admin_user.is_superuser,
                    )
                )
                return admin_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'.",
        )

    token = parts[1]
    session_rec = db.scalar(
        select(SessionRecord).where(
            (SessionRecord.session_token == token)
            & (SessionRecord.revoked_at.is_(None))
            & (SessionRecord.expires_at > datetime.utcnow())
        )
    )

    if not session_rec or not session_rec.user or not session_rec.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired, revoked, or invalid.",
        )

    set_tenant_context(
        TenantContext(
            tenant_id=session_rec.tenant_id,
            user_id=session_rec.user_id,
            is_superuser=session_rec.user.is_superuser,
        )
    )

    return session_rec.user

