from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import jwt
import bcrypt as _bcrypt

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.identity import User


ROLE_PERMISSIONS = {
    "admin": {"read", "write", "manage_users", "manage_roles"},
    "pentester": {"read", "write"},
    "auditor": {"read", "audit"},
}

# In-memory user store (small projects / tests). Replace with persistent storage later.
_USERS: dict[str, dict[str, Any]] = {}


def register_user(username: str, password: str, role: str = "pentester") -> dict[str, Any]:
    if username in _USERS:
        raise ValueError("User already exists")
    # bcrypt.hashpw returns bytes; store utf-8 string
    hashed = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
    user = {
        "username": username,
        "password_hash": hashed,
        "role": role,
        "created_at": datetime.utcnow().isoformat(),
    }
    # persist to database if available
    try:
        db = SessionLocal()
        # ensure role exists is handled elsewhere; we store username and hash
        db_user = User(username=username, password_hash=hashed)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception:
        # fall back to in-memory if DB not available
        _USERS[username] = user
    return {"username": username, "role": role}


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    # Try DB first
    try:
        db = SessionLocal()
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            ok = _bcrypt.checkpw(password.encode("utf-8"), db_user.password_hash.encode("utf-8"))
            if ok:
                return {"username": db_user.username, "role": db_user.role.name if db_user.role else "pentester"}
            return None
    except Exception:
        pass
    user = _USERS.get(username)
    if not user:
        return None
    try:
        ok = _bcrypt.checkpw(password.encode("utf-8"), user.get("password_hash", "").encode("utf-8"))
    except Exception:
        return None
    if not ok:
        return None
    return user


def create_access_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.algorithm])


def can_access(user_role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(user_role, set())
