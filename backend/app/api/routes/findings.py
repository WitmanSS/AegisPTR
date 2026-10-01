from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import require_permission
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.finding import Finding
from app.schemas.finding import FindingCreate
from app.services.finding_correlation import correlate_findings
from app.services.risk_engine import risk_engine

router = APIRouter(prefix="/findings", tags=["findings"])


def serialize_finding(finding: Finding) -> dict:
    try:
        evidence = json.loads(finding.evidence or "[]")
    except (TypeError, json.JSONDecodeError):
        evidence = [finding.evidence] if finding.evidence else []
    if not isinstance(evidence, list):
        evidence = [evidence]
    return {
        "finding_id": finding.finding_id,
        "assessment_id": finding.assessment_id,
        "title": finding.title,
        "description": finding.description,
        "category": finding.category,
        "cve": finding.cve,
        "cwe": finding.cwe,
        "cvss": finding.cvss,
        "severity": finding.severity,
        "asset": finding.asset,
        "ip": finding.ip,
        "hostname": finding.hostname,
        "url": finding.url,
        "port": finding.port,
        "protocol": finding.protocol,
        "service": finding.service,
        "source_tool": finding.source_tool,
        "validation_status": finding.validation_status,
        "confidence": finding.confidence,
        "exploitability": finding.exploitability,
        "exposure": finding.exposure,
        "business_impact": finding.business_impact,
        "risk_score": finding.risk_score,
        "priority": finding.priority,
        "status": finding.status,
        "evidence": evidence,
        "remediation": finding.remediation,
        "created_at": finding.created_at.isoformat() if finding.created_at else None,
        "updated_at": finding.updated_at.isoformat() if finding.updated_at else None,
    }


@router.get("")
async def list_findings(
    q: str | None = Query(default=None, max_length=200),
    severity: str | None = None,
    status: str | None = None,
    assessment_id: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(require_permission("read")),
) -> list[dict]:
    statement = select(Finding).order_by(Finding.risk_score.desc(), Finding.created_at.desc())
    if q:
        statement = statement.where(
            Finding.title.ilike(f"%{q}%")
            | Finding.asset.ilike(f"%{q}%")
            | Finding.cve.ilike(f"%{q}%")
            | Finding.source_tool.ilike(f"%{q}%")
        )
    if severity:
        statement = statement.where(Finding.severity.ilike(severity))
    if status:
        statement = statement.where(Finding.status.ilike(status))
    if assessment_id:
        statement = statement.where(Finding.assessment_id == assessment_id)
    rows = db.execute(statement.offset((page - 1) * size).limit(size)).scalars().all()
    return [serialize_finding(row) for row in rows]


@router.get("/explorer")
async def findings_explorer(
    q: str | None = Query(default=None, max_length=200),
    severity: str | None = None,
    status: str | None = None,
    assessment_id: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(require_permission("read")),
) -> dict:
    statement = select(Finding)
    filters = []
    if q:
        filters.append(Finding.title.ilike(f"%{q}%") | Finding.asset.ilike(f"%{q}%") | Finding.cve.ilike(f"%{q}%") | Finding.source_tool.ilike(f"%{q}%"))
    if severity:
        filters.append(Finding.severity.ilike(severity))
    if status:
        filters.append(Finding.status.ilike(status))
    if assessment_id:
        filters.append(Finding.assessment_id == assessment_id)
    if filters:
        from sqlalchemy import and_
        statement = statement.where(and_(*filters))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.execute(statement.order_by(Finding.risk_score.desc(), Finding.created_at.desc()).offset((page - 1) * size).limit(size)).scalars().all()
    return {"items": [serialize_finding(row) for row in rows], "page": {"page": page, "size": size, "total": total}}


@router.get("/correlations")
async def list_correlations(
    assessment_id: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_permission("read")),
) -> dict:
    statement = select(Finding).order_by(Finding.risk_score.desc(), Finding.created_at.desc())
    if assessment_id:
        statement = statement.where(Finding.assessment_id == assessment_id)
    findings = [serialize_finding(row) for row in db.execute(statement).scalars().all()]
    groups = correlate_findings(findings)
    if severity:
        groups = [group for group in groups if group["severity"].upper() == severity.upper()]
    if status:
        groups = [group for group in groups if status.upper() in group["statuses"]]
    return {"items": groups, "total": len(groups)}


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
        finding_id = f"F-{uuid4().hex[:12].upper()}"
        evidence = normalized.pop("evidence", [])
        risk_score = risk_engine.calculate_risk_score(normalized)
        priority = risk_engine.determine_priority(risk_score)
        finding = Finding(
            finding_id=finding_id,
            assessment_id=assessment_id,
            title=normalized["title"],
            description=normalized.get("description"),
            category=normalized.get("category"),
            cve=normalized.get("cve"),
            cwe=normalized.get("cwe"),
            cvss=normalized.get("cvss"),
            severity=normalized.get("severity", "MEDIUM"),
            asset=normalized.get("asset"),
            ip=normalized.get("ip"),
            hostname=normalized.get("hostname"),
            url=normalized.get("url"),
            port=normalized.get("port"),
            protocol=normalized.get("protocol"),
            service=normalized.get("service"),
            source_tool=normalized.get("source_tool"),
            validation_status=normalized.get("validation_status", "UNVERIFIED"),
            confidence=normalized.get("confidence", 0),
            exploitability=normalized.get("exploitability"),
            exposure=normalized.get("exposure"),
            business_impact=normalized.get("business_impact"),
            risk_score=risk_score,
            priority=priority,
            status=normalized.get("status", "OPEN"),
            evidence=json.dumps(evidence),
            remediation=normalized.get("remediation"),
        )
        db.add(finding)
        saved.append({"finding_id": finding_id, **normalized, "risk_score": risk_score, "priority": priority, "evidence": evidence, "assessment_id": assessment_id})

    db.commit()

    return {"assessment_id": assessment_id, "saved": saved}


@router.post("/{finding_id}/actions")
async def perform_finding_action(
    finding_id: str,
    body: dict,
    db: Session = Depends(get_db),
    user=Depends(require_permission("write")),
) -> dict:
    action = str(body.get("action", "")).strip().lower()
    finding = db.scalar(select(Finding).where(Finding.finding_id == finding_id))
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    if action == "set_status":
        next_status = str(body.get("status", "")).strip().upper()
        allowed_statuses = {"OPEN", "TRIAGED", "IN_PROGRESS", "RESOLVED", "SUPPRESSED"}
        if next_status not in allowed_statuses:
            raise HTTPException(status_code=400, detail=f"status must be one of {sorted(allowed_statuses)}")
        finding.status = next_status
        db.commit()
        db.refresh(finding)
        return {"status": "updated", "finding": serialize_finding(finding)}
    raise HTTPException(status_code=400, detail="Supported action: set_status")
