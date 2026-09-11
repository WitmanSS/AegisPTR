from fastapi import APIRouter, Depends

from app.core.tool_registry import get_available_adapters
from app.api.deps import require_permission

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/inventory")
async def inventory(user=Depends(require_permission("read"))) -> dict:
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
