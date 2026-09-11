from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends

from app.api.deps import require_permission

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
            })
    return queued


@router.post("")
async def create_task(payload: dict, user=Depends(require_permission("write"))) -> dict:
    assessment_id = str(payload.get("assessment_id", "")).strip()
    tool_id = str(payload.get("tool_id", "nmap")).strip()
    target = str(payload.get("target", "")).strip()
    if not assessment_id or not target:
        raise HTTPException(status_code=400, detail="assessment_id and target are required")

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
async def execute_task(task_id: str, user=Depends(require_permission("write"))) -> dict:
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

    executed = await orchestrator.run(task)
    return {
        "task_id": executed.task_id,
        "assessment_id": executed.assessment_id,
        "tool_id": executed.tool_id,
        "status": executed.status,
        "parsed_results": executed.parsed_results,
        "exit_code": executed.exit_code,
    }
