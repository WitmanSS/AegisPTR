from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import decode_access_token
from app.models.identity import User


def get_db_session() -> Session:
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.username == username).first()
    if user is None or user.disabled:
        raise HTTPException(status_code=401, detail="User not found or disabled")
    return user


def require_permission(permission: str):
    def _checker(user: User = Depends(get_current_user)) -> User:
        # simple role->permission mapping live in auth_service
        from app.services.auth_service import can_access

        role_name = user.role.name if user.role else ""
        if not can_access(role_name, permission):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _checker
