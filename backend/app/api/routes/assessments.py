from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment, AssessmentScope
from app.schemas.assessment import AssessmentCreate, AssessmentRead
from app.services.orchestrator import ToolTask, orchestrator

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=list[AssessmentRead])
async def list_assessments(db: Session = Depends(get_db)) -> list[AssessmentRead]:
    assessments = db.execute(select(Assessment).order_by(Assessment.created_at.desc())).scalars().all()
    return [
        AssessmentRead(
            id=item.id,
            name=item.name,
            client=item.client,
            assessment_type=item.assessment_type,
            status=item.status,
            scope_text=item.scope_text,
            exclusions=item.exclusions,
            is_authorized=item.is_authorized,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in assessments
    ]


@router.post("", response_model=AssessmentRead)
async def create_assessment(
    payload: AssessmentCreate,
    db: Session = Depends(get_db),
) -> AssessmentRead:
    assessment = Assessment(
        name=payload.name,
        client=payload.client,
        assessment_type=payload.assessment_type,
        status=payload.status,
        scope_text="; ".join(payload.scope),
        exclusions="; ".join(payload.exclusions),
        is_authorized=payload.status.upper() == "AUTHORIZED",
    )
    db.add(assessment)
    db.flush()

    for target in payload.scope:
        db.add(
            AssessmentScope(
                assessment_id=assessment.id,
                target=target,
                kind="cidr" if "/" in target else "host",
                allowed=True,
            )
        )

    for target in payload.exclusions:
        db.add(
            AssessmentScope(
                assessment_id=assessment.id,
                target=target,
                kind="exclude",
                allowed=False,
            )
        )

    db.commit()
    db.refresh(assessment)

    return AssessmentRead(
        id=assessment.id,
        name=assessment.name,
        client=assessment.client,
        assessment_type=assessment.assessment_type,
        status=assessment.status,
        scope_text=assessment.scope_text,
        exclusions=assessment.exclusions,
        is_authorized=assessment.is_authorized,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
    )


@router.post("/{assessment_id}/authorize")
async def authorize_assessment(
    assessment_id: str,
    body: dict,
    db: Session = Depends(get_db),
) -> dict:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    authorized = bool(body.get("authorized", False))
    assessment.is_authorized = authorized
    assessment.status = "AUTHORIZED" if authorized else "DRAFT"
    db.commit()
    db.refresh(assessment)

    return {
        "id": assessment.id,
        "name": assessment.name,
        "status": assessment.status,
        "is_authorized": assessment.is_authorized,
    }


@router.post("/{assessment_id}/tasks")
async def create_assessment_task(
    assessment_id: str,
    body: dict,
    db: Session = Depends(get_db),
) -> dict:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    tool_id = str(body.get("tool_id", "nmap")).strip()
    target = str(body.get("target", "")).strip()
    if not target:
        raise HTTPException(status_code=400, detail="Target is required")

    task = ToolTask(
        task_id=str(uuid4()),
        assessment_id=assessment_id,
        tool_id=tool_id,
        target=target,
        status="QUEUED",
        parsed_results=[],
    )
    await orchestrator.enqueue(task)

    return {
        "task_id": task.task_id,
        "assessment_id": assessment_id,
        "tool_id": tool_id,
        "target": target,
        "status": task.status,
    }
