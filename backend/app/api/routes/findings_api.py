from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List

from app.schemas.finding_api import FindingFull, FindingsListResponse
from app.api.deps import get_db, require_permission

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("", response_model=FindingsListResponse)
async def list_findings_api(page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=200), user=Depends(require_permission("read"))):
    """Paged findings list (stub implementation)."""
    # TODO: implement DB-backed listing with filters, search, sorting
    return FindingsListResponse(items=[], page={"page": page, "size": size, "total": 0})


@router.get("/{finding_id}", response_model=FindingFull)
async def get_finding(finding_id: str, user=Depends(require_permission("read"))):
    """Return full finding detail (stub)."""
    # TODO: load from DB
    raise HTTPException(status_code=404, detail="Finding not found (stub)")


@router.post("/{finding_id}/actions")
async def perform_finding_action(finding_id: str, body: dict, user=Depends(require_permission("write"))):
    """Perform action on a finding (assign, create_remediation, suppress, retest, split, merge)."""
    action = body.get("action")
    if not action:
        raise HTTPException(status_code=400, detail="action is required")
    # TODO: dispatch to action handlers
    return {"status": "accepted", "finding_id": finding_id, "action": action}


@router.post("/bulk/actions")
async def bulk_actions(body: dict, user=Depends(require_permission("write"))):
    """Bulk operations for findings (stub)."""
    actions = body.get("actions", [])
    if not isinstance(actions, list):
        raise HTTPException(status_code=400, detail="actions must be a list")
    # TODO: implement bulk handling with job queue
    return {"status": "accepted", "count": len(actions)}
