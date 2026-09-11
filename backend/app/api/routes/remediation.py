from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.remediation_engine import remediation_engine

router = APIRouter(prefix="/remediation", tags=["remediation"])


@router.get("/plans")
async def list_remediation_plans() -> list[dict]:
    return remediation_engine.list_plans()


@router.post("/generate")
async def generate_remediation(payload: dict) -> dict:
    assessment_id = str(payload.get("assessment_id", "")).strip()
    finding_ids = payload.get("finding_ids", [])
    assignee = str(payload.get("assignee", "security-team")).strip() or "security-team"

    if not assessment_id:
        raise HTTPException(status_code=400, detail="assessment_id is required")
    if not isinstance(finding_ids, list) or not finding_ids:
        raise HTTPException(status_code=400, detail="finding_ids must be a non-empty list")

    plan = remediation_engine.generate(assessment_id=assessment_id, finding_ids=[str(item) for item in finding_ids], assignee=assignee)
    return {
        "plan_id": plan.plan_id,
        "assessment_id": plan.assessment_id,
        "assignee": plan.assignee,
        "status": plan.status,
        "tasks": [task.to_dict() for task in plan.tasks],
    }
