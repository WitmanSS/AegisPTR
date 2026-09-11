from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import require_permission
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment
from app.schemas.finding import FindingCreate

router = APIRouter(prefix="/findings", tags=["findings"])

_FALLBACK_FINDINGS: list[dict] = []


@router.get("")
async def list_findings(db: Session = Depends(get_db), user=Depends(require_permission("read"))) -> list[dict]:
    if not _FALLBACK_FINDINGS:
        rows = db.execute(select(Assessment)).scalars().all()
        if not rows:
            return []
    return [
        {
            "finding_id": f"F-{idx + 1:03d}",
            "title": item.get("title", "Untitled finding"),
            "description": item.get("description"),
            "severity": item.get("severity", "MEDIUM"),
            "risk_score": item.get("risk_score", 0),
            "asset": item.get("asset"),
            "status": item.get("status", "OPEN"),
            "source_tool": item.get("source_tool"),
        }
        for idx, item in enumerate(_FALLBACK_FINDINGS)
    ]


@router.post("/ingest")
async def ingest_findings(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_permission("write")),
) -> dict:
    assessment_id = str(payload.get("assessment_id", "")).strip()
    if not assessment_id:
        raise HTTPException(status_code=400, detail="assessment_id is required")

    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    records = payload.get("findings", [])
    if not isinstance(records, list):
        raise HTTPException(status_code=400, detail="findings must be a list")

    saved: list[dict] = []
    for item in records:
        normalized = FindingCreate(**item).model_dump()
        normalized["finding_id"] = f"F-{len(saved) + 1:03d}"
        normalized["assessment_id"] = assessment_id
        normalized["created_at"] = normalized.get("created_at") if "created_at" in normalized else None
        normalized["updated_at"] = normalized.get("updated_at") if "updated_at" in normalized else None
        saved.append(normalized)
        _FALLBACK_FINDINGS.append({
            "title": normalized["title"],
            "description": normalized.get("description"),
            "severity": normalized.get("severity", "MEDIUM"),
            "risk_score": normalized.get("risk_score", 0),
            "asset": normalized.get("asset"),
            "status": normalized.get("status", "OPEN"),
            "source_tool": normalized.get("source_tool"),
        })

    return {"assessment_id": assessment_id, "saved": saved}
