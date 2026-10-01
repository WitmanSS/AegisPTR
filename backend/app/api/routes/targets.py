from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import require_permission
from app.core.database import get_db
from app.services.target_service import parse_bulk, validate_target, normalize_target
from app.schemas.target import (
    BulkParseRequest,
    BulkParseResponse,
    TargetCreate,
    TargetOut,
    BulkCreateRequest,
    BulkCreateResponse,
)
from app.models.assessment import Assessment, AssessmentScope
from app.models.finding import Finding

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
    from app.models.target import Target

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
    from app.models.target import Target

    q = db.query(Target).limit(limit).offset(offset).all()
    return q


@router.get("/graph")
def attack_surface_graph(
    assessment_id: str | None = None,
    severity: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_permission("read")),
) -> dict:
    """Return explicit persisted assessment, target, service and finding relationships."""
    from urllib.parse import urlsplit

    node_map: dict[str, dict] = {}
    edge_map: dict[str, dict] = {}

    def add_node(node: dict) -> str:
        node_map.setdefault(node["data"]["id"], node)
        return node["data"]["id"]

    def add_edge(source: str, target: str, relation: str) -> None:
        edge_id = f"{source}|{relation}|{target}"
        edge_map.setdefault(edge_id, {"data": {"id": edge_id, "source": source, "target": target, "relation": relation}})

    assessments_query = db.query(Assessment)
    if assessment_id:
        assessments_query = assessments_query.filter(Assessment.id == assessment_id)
    assessments = assessments_query.order_by(Assessment.created_at.desc()).limit(100).all()
    assessments_by_id = {item.id: item for item in assessments}
    scopes_query = db.query(AssessmentScope).filter(AssessmentScope.assessment_id.in_(assessments_by_id)) if assessments_by_id else None
    scope_rows = scopes_query.all() if scopes_query is not None else []
    from app.models.target import Target

    target_rows = db.query(Target).order_by(Target.updated_at.desc()).limit(1000).all()
    targets_by_key: dict[str, Target] = {item.canonical.strip().lower().rstrip("/"): item for item in target_rows}
    scope_target_keys = {row.target.strip().lower().rstrip("/") for row in scope_rows if row.allowed}

    for assessment in assessments:
        add_node({"data": {"id": f"assessment:{assessment.id}", "kind": "assessment", "label": assessment.name, "status": assessment.status, "authorized": assessment.is_authorized, "assessment_id": assessment.id}})

    for scope in scope_rows:
        normalized = scope.target.strip().lower().rstrip("/")
        target_row = targets_by_key.get(normalized)
        target_id = f"target:{target_row.id}" if target_row else f"scope:{normalized}"
        hostname = urlsplit(scope.target).hostname
        label = target_row.canonical if target_row else (hostname or scope.target)
        add_node({"data": {
            "id": target_id, "kind": "target", "label": label,
            "target_type": target_row.target_type if target_row else scope.kind,
            "authorization_status": target_row.authorization_status if target_row else ("AUTHORIZED" if scope.allowed and assessments_by_id.get(scope.assessment_id, None) and assessments_by_id[scope.assessment_id].is_authorized else "PENDING"),
            "scope_status": target_row.scope_status if target_row else ("IN_SCOPE" if scope.allowed else "EXCLUDED"),
            "environment": target_row.environment if target_row else None,
            "criticality": target_row.criticality if target_row else None,
            "owner": target_row.owner if target_row else None,
            "target_key": normalized,
        }})
        assessment_node_id = f"assessment:{scope.assessment_id}"
        if assessment_node_id in node_map:
            add_edge(assessment_node_id, target_id, "allows" if scope.allowed else "excludes")

    for target in target_rows:
        normalized = target.canonical.strip().lower().rstrip("/")
        if normalized not in scope_target_keys:
            continue
        target_id = f"target:{target.id}"
        add_node({"data": {
            "id": target_id, "kind": "target", "label": target.canonical,
            "target_type": target.target_type, "authorization_status": target.authorization_status,
            "scope_status": target.scope_status, "environment": target.environment,
            "criticality": target.criticality, "owner": target.owner, "target_key": normalized,
        }})

    findings_query = db.query(Finding)
    if assessment_id:
        findings_query = findings_query.filter(Finding.assessment_id == assessment_id)
    if severity:
        findings_query = findings_query.filter(Finding.severity.ilike(severity))
    findings = findings_query.order_by(Finding.risk_score.desc()).limit(2000).all()
    target_ids_by_alias: dict[str, str] = {}
    for node_id, node in node_map.items():
        if node["data"].get("kind") == "target":
            target_ids_by_alias[node["data"].get("target_key", "")] = node_id
            target_label = str(node["data"].get("label", "")).strip().lower().rstrip("/")
            target_ids_by_alias[target_label] = node_id
            host = urlsplit(target_label).hostname
            if host:
                target_ids_by_alias[host.lower()] = node_id

    for finding in findings:
        asset_aliases = [finding.asset, finding.hostname, finding.ip, finding.url]
        matched_target_id = next((target_ids_by_alias.get(alias.strip().lower().rstrip("/")) for alias in asset_aliases if alias and target_ids_by_alias.get(alias.strip().lower().rstrip("/"))), None)
        finding_id = f"finding:{finding.finding_id}"
        add_node({"data": {
            "id": finding_id, "kind": "finding", "label": finding.title,
            "finding_id": finding.finding_id, "severity": finding.severity,
            "risk_score": finding.risk_score, "status": finding.status,
            "cve": finding.cve, "source_tool": finding.source_tool,
            "assessment_id": finding.assessment_id,
        }})
        if matched_target_id:
            add_edge(matched_target_id, finding_id, "observed finding")
            if finding.port:
                service_key = f"{matched_target_id}:{finding.protocol or 'tcp'}:{finding.port}"
                service_id = f"service:{service_key}"
                service_label = f"{finding.port}/{finding.protocol or 'tcp'}{f' · {finding.service}' if finding.service else ''}"
                add_node({"data": {"id": service_id, "kind": "service", "label": service_label, "port": finding.port, "protocol": finding.protocol or "tcp", "service": finding.service, "assessment_id": finding.assessment_id}})
                add_edge(matched_target_id, service_id, "observed service")
                add_edge(service_id, finding_id, "associated finding")

    if q:
        needle = q.strip().lower()
        matched_ids = {node_id for node_id, node in node_map.items() if needle in str(node["data"].get("label", "")).lower() or needle in str(node["data"].get("cve", "")).lower()}
        connected_ids = set(matched_ids)
        for edge in edge_map.values():
            if edge["data"]["source"] in matched_ids or edge["data"]["target"] in matched_ids:
                connected_ids.add(edge["data"]["source"])
                connected_ids.add(edge["data"]["target"])
        node_map = {node_id: node for node_id, node in node_map.items() if node_id in connected_ids}
        edge_map = {edge_id: edge for edge_id, edge in edge_map.items() if edge["data"]["source"] in node_map and edge["data"]["target"] in node_map}

    return {"elements": {"nodes": list(node_map.values()), "edges": list(edge_map.values())}, "counts": {"nodes": len(node_map), "edges": len(edge_map)}}



@router.post("/bulk", response_model=BulkCreateResponse)
def bulk_create(body: BulkCreateRequest, db: Session = Depends(get_db), _=Depends(require_permission("write"))):
    """Create multiple targets transactionally. Returns per-item status summary."""
    from app.models.target import Target, TargetHistory
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
