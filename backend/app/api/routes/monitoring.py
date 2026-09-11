from __future__ import annotations

from fastapi import APIRouter

from app.services.kpi_engine import kpi_engine

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/summary")
async def monitoring_summary() -> dict:
    return kpi_engine.summary()
