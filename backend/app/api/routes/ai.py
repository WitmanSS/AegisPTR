from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def ai_status() -> dict:
    return {
        "provider": "disabled",
        "mode": "local",
        "status": "not_configured",
    }
