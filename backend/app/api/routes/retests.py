from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.retest_engine import retest_engine

router = APIRouter(prefix="/retests", tags=["retests"])


@router.get("")
async def list_retests() -> list[dict]:
    return retest_engine.list_records()


@router.post("")
async def create_retest(payload: dict) -> dict:
    assessment_id = str(payload.get("assessment_id", "")).strip()
    finding_id = str(payload.get("finding_id", "")).strip()
    retest_type = str(payload.get("retest_type", "POST_REMEDIATION")).strip() or "POST_REMEDIATION"
    status = str(payload.get("status", "PENDING")).strip() or "PENDING"

    if not assessment_id:
        raise HTTPException(status_code=400, detail="assessment_id is required")
    if not finding_id:
        raise HTTPException(status_code=400, detail="finding_id is required")

    record = retest_engine.create(assessment_id, finding_id, retest_type, status)
    return record.to_dict()


@router.post("/{retest_id}/validate")
async def validate_retest(retest_id: str, payload: dict) -> dict:
    passed = bool(payload.get("passed", False))
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list):
        raise HTTPException(status_code=400, detail="evidence must be a list")

    try:
        record = retest_engine.validate(retest_id, passed, [str(item) for item in evidence])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return record.to_dict()
