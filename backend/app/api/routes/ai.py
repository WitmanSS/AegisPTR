from fastapi import APIRouter, Depends

from app.api.deps import require_permission

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def ai_status(user=Depends(require_permission("read"))) -> dict:
    return {
        "provider": "disabled",
        "mode": "local",
        "status": "not_configured",
    }
