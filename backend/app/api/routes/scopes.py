from fastapi import APIRouter, Depends

from app.services.scope_engine import scope_engine
from app.api.deps import require_permission

router = APIRouter(prefix="/scopes", tags=["scopes"])


@router.post("/validate")
async def validate_scope(payload: dict, user=Depends(require_permission("read"))) -> dict:
    target = payload.get("target", "")
    allowed = payload.get("allowed", [])
    excluded = payload.get("excluded", [])
    is_valid = scope_engine.validate_target(target, allowed, excluded)
    return {
        "target": target,
        "allowed": allowed,
        "excluded": excluded,
        "in_scope": is_valid,
        "status": "ALLOW" if is_valid else "BLOCK",
    }
