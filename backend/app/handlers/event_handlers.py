from typing import Any, Dict
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4
import json

try:
    # import the AuditLog model from identity models
    from backend.app.models.identity import AuditLog
except Exception:
    AuditLog = None

try:
    from backend.app.models.finding import Finding
except Exception:
    Finding = None


def _create_finding_from_event(db: Session, event: Dict[str, Any]):
    data = event.get("data") or {}
    title = data.get("title") or data.get("name") or "Untitled finding"
    description = data.get("description") or data.get("details")
    finding_id = data.get("id") or data.get("finding_id")

    if Finding is None:
        return {"title": title, "description": description, "finding_id": finding_id}

    f = Finding(
        finding_id=finding_id or str(uuid4()),
        title=title,
        description=description,
        category=data.get("category"),
        severity=data.get("severity", "MEDIUM"),
        asset=data.get("asset"),
        ip=data.get("ip"),
        hostname=data.get("hostname"),
        url=data.get("url"),
        port=data.get("port"),
        source_tool=event.get("source") or data.get("source_tool"),
        validation_status=data.get("validation_status", "UNVERIFIED"),
        confidence=data.get("confidence", 0),
        risk_score=data.get("risk_score", 0),
        status=data.get("status", "OPEN"),
        evidence=json.dumps(data.get("evidence", [])),
        remediation=data.get("remediation"),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def handle_event(db: Session, event: Dict[str, Any]):
    """Event handler: persist event to AuditLog and create Findings for observations.

    Recognizes simple observation/scan events and creates a Finding record.
    More advanced correlation will be implemented in worker processes.
    """
    payload = json.dumps(event)
    now = datetime.utcnow()

    # persist audit log if available
    if AuditLog is not None:
        log = AuditLog(action=event.get("type", "event"), details=payload, created_at=now)
        db.add(log)
        db.commit()
        db.refresh(log)
    else:
        log = None

    # simple correlation: create a finding for observation or tool output
    etype = event.get("type", "").lower()
    created_finding = None
    if "observation" in etype or "finding" in etype or "scan.result" in etype or "tool." in etype:
        created_finding = _create_finding_from_event(db, event)
        # publish downstream event for consumers/workers
        try:
            from backend.app.events.publisher import publish_event

            publish_event("finding.created", {"type": "finding.created", "data": getattr(created_finding, "id", created_finding) or created_finding})
        except Exception:
            # best-effort: don't fail handler if publisher isn't available
            pass

    return {"audit": getattr(log, "id", None), "finding": getattr(created_finding, "id", created_finding)}
