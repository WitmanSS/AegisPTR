from fastapi import APIRouter

from app.core.tool_registry import get_available_adapters

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/inventory")
async def inventory() -> dict:
    available = get_available_adapters()
    return {
        "tools": {
            name: {
                "available": True,
                "status": "ready",
                "version": adapter.version,
            }
            for name, adapter in available.items()
        }
    }
