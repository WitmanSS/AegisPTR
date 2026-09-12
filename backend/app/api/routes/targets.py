from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from backend.app.api.deps import require_permission
from backend.app.core.database import get_db
from backend.app.services.target_service import parse_bulk, validate_target, normalize_target
from backend.app.schemas.target import (
    BulkParseRequest,
    BulkParseResponse,
    TargetCreate,
    TargetOut,
    BulkCreateRequest,
    BulkCreateResponse,
)

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.post("/bulk/preview", response_model=BulkParseResponse)
def bulk_preview(body: BulkParseRequest, db: Session = Depends(get_db), _=Depends(require_permission("write"))):
    """Parse and validate a pasted list of targets and return a preview before saving."""
    result = parse_bulk(body.text)
    return result


@router.post("/validate")
def validate_single(target: dict, db: Session = Depends(get_db), _=Depends(require_permission("write"))):
    value = target.get("value")
    if not value:
        raise HTTPException(status_code=400, detail="missing value")
    return validate_target(value, resolve=target.get("resolve", False))


@router.post("/", response_model=TargetOut)
def create_target(t: TargetCreate, db: Session = Depends(get_db), _=Depends(require_permission("write"))):
    from backend.app.models.target import Target

    obj = Target(
        original=t.original,
        canonical=t.canonical or normalize_target(t.original).get("canonical") or t.original,
        target_type=t.target_type or normalize_target(t.original).get("type") or "unknown",
        protocol=t.protocol,
        hostname=t.hostname,
        ip=t.ip,
        port=t.port,
        path=t.path,
        environment=t.environment,
        business_unit=t.business_unit,
        criticality=t.criticality,
        owner=t.owner,
        authorization_status=t.authorization_status or "UNAUTHORIZED",
        scope_status=t.scope_status or "DRAFT",
        tags=",".join(t.tags) if t.tags else None,
        notes=t.notes,
        valid_from=t.valid_from,
        valid_until=t.valid_until,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/")
def list_targets(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), _=Depends(require_permission("read"))):
    from backend.app.models.target import Target

    q = db.query(Target).limit(limit).offset(offset).all()
    return q



@router.post("/bulk", response_model=BulkCreateResponse)
def bulk_create(body: BulkCreateRequest, db: Session = Depends(get_db), _=Depends(require_permission("write"))):
    """Create multiple targets transactionally. Returns per-item status summary."""
    from backend.app.models.target import Target, TargetHistory
    items = body.items
    results = []
    created = 0
    failed = 0

    for itm in items:
        original = itm.original
        try:
            canonical = itm.canonical or normalize_target(original).get("canonical") or original
            target_type = itm.target_type or normalize_target(original).get("type") or "unknown"
            obj = Target(
                original=original,
                canonical=canonical,
                target_type=target_type,
                protocol=itm.protocol,
                hostname=itm.hostname,
                ip=itm.ip,
                port=itm.port,
                path=itm.path,
                environment=itm.environment,
                business_unit=itm.business_unit,
                criticality=itm.criticality,
                owner=itm.owner,
                authorization_status=itm.authorization_status or "UNAUTHORIZED",
                scope_status=itm.scope_status or "DRAFT",
                tags=",".join(itm.tags) if itm.tags else None,
                notes=itm.notes,
                valid_from=itm.valid_from,
                valid_until=itm.valid_until,
            )
            db.add(obj)
            db.flush()
            # history
            hist = TargetHistory(target_id=obj.id, action="created", details=f"created from bulk import")
            db.add(hist)
            db.commit()
            db.refresh(obj)
            results.append({"original": original, "id": obj.id, "status": "created", "error": None})
            created += 1
        except Exception as e:
            db.rollback()
            results.append({"original": original, "id": None, "status": "failed", "error": str(e)})
            failed += 1

    return {"total": len(items), "created": created, "failed": failed, "items": results}
