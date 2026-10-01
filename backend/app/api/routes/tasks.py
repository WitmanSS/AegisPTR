from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.assessment import Assessment
from app.services.operation_scope import is_target_authorized

from app.services.orchestrator import ToolTask, orchestrator

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(user=Depends(require_permission("read"))) -> list[dict]:
    queued = []
    for tasks in orchestrator._queues.values():
        for task in tasks:
            queued.append({
                "task_id": task.task_id,
                "assessment_id": task.assessment_id,
                "tool_id": task.tool_id,
                "target": task.target,
                "status": task.status,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "ended_at": task.ended_at.isoformat() if task.ended_at else None,
                "exit_code": task.exit_code,
                "parsed_results": task.parsed_results,
                "stdout": task.stdout[-5000:],
                "stderr": task.stderr[-5000:],
            })
    return queued


@router.post("")
async def create_task(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_permission("write")),
) -> dict:
    assessment_id = str(payload.get("assessment_id", "")).strip()
    tool_id = str(payload.get("tool_id", "nmap")).strip()
    target = str(payload.get("target", "")).strip()
    if not assessment_id or not target:
        raise HTTPException(status_code=400, detail="assessment_id and target are required")

    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.is_authorized:
        raise HTTPException(status_code=403, detail="Assessment scope is not authorized")
    if not is_target_authorized(assessment, target):
        raise HTTPException(status_code=403, detail="Target is outside the authorized assessment scope")

    task = ToolTask(
        task_id=str(uuid4()),
        assessment_id=assessment_id,
        tool_id=tool_id,
        target=target,
        status="QUEUED",
    )
    await orchestrator.enqueue(task)

    return {
        "task_id": task.task_id,
        "assessment_id": assessment_id,
        "tool_id": tool_id,
        "target": target,
        "status": task.status,
    }


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_permission("write")),
) -> dict:
    task = None
    for queue in orchestrator._queues.values():
        for item in queue:
            if item.task_id == task_id:
                task = item
                break
        if task is not None:
            break

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "QUEUED":
        raise HTTPException(status_code=409, detail=f"Task cannot run from status {task.status}")

    assessment = db.get(Assessment, task.assessment_id)
    if assessment is None or not assessment.is_authorized:
        raise HTTPException(status_code=403, detail="Assessment is no longer authorized")
    if not is_target_authorized(assessment, task.target):
        raise HTTPException(status_code=403, detail="Target is outside the authorized assessment scope")

    executed = await orchestrator.run(task)
    return {
        "task_id": executed.task_id,
        "assessment_id": executed.assessment_id,
        "tool_id": executed.tool_id,
        "status": executed.status,
        "parsed_results": executed.parsed_results,
        "exit_code": executed.exit_code,
    }
