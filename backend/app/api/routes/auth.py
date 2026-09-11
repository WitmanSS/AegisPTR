from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header

from app.services.auth_service import authenticate_user, can_access, create_access_token, decode_access_token, register_user

router = APIRouter(tags=["auth"])


@router.post("/auth/register")
async def register(payload: dict) -> dict:
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()
    role = str(payload.get("role", "pentester")).strip() or "pentester"
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")
    try:
        user = register_user(username, password, role)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return user


@router.post("/auth/login")
async def login(payload: dict) -> dict:
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()
    user = authenticate_user(username, password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["username"], user["role"])
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}


@router.get("/auth/me")
async def me(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception as exc:  # pragma: no cover - jwt-specific branch
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    return {"username": payload["sub"], "role": payload["role"]}


@router.get("/admin/metrics")
async def admin_metrics(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception as exc:  # pragma: no cover - jwt-specific branch
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    if not can_access(payload["role"], "manage_users"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"status": "ok", "metrics": {"assessments": 22, "findings": 148}}
