from __future__ import annotations

from fastapi import APIRouter, Depends

from app.services.kpi_engine import kpi_engine
from app.api.deps import require_permission

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/summary")
async def monitoring_summary(user=Depends(require_permission("read"))) -> dict:
    return kpi_engine.summary()
