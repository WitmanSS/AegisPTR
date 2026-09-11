from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.adapters.nmap.adapter import NmapAdapter
from app.adapters.nuclei.adapter import NucleiAdapter
from app.adapters.zap.adapter import ZAPAdapter


@dataclass
class ToolTask:
    task_id: str
    assessment_id: str
    tool_id: str
    target: str
    status: str = "QUEUED"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    parsed_results: list[dict[str, Any]] = field(default_factory=list)


class ToolOrchestrator:
    def __init__(self) -> None:
        self._queues: dict[str, list[ToolTask]] = {}
        self._tool_map = {
            "nmap": NmapAdapter(),
            "nuclei": NucleiAdapter(),
            "zap": ZAPAdapter(),
        }

    async def enqueue(self, task: ToolTask, queue_name: str = "default") -> None:
        self._queues.setdefault(queue_name, [])
        self._queues[queue_name].append(task)

    async def run(self, task: ToolTask) -> ToolTask:
        adapter = self._tool_map.get(task.tool_id)
        if adapter is None:
            task.status = "SKIPPED"
            task.exit_code = 1
            task.ended_at = datetime.utcnow()
            task.parsed_results = [{"tool": task.tool_id, "title": "Unsupported tool", "severity": "INFO"}]
            return task

        task.status = "RUNNING"
        task.started_at = datetime.utcnow()
        await asyncio.sleep(0)

        result = adapter.execute(task.target, {"fast": True})
        task.stdout = result.get("stdout", "")
        task.stderr = result.get("stderr", "")
        task.exit_code = result.get("returncode")

        if not result.get("success"):
            task.status = "SKIPPED"
            task.ended_at = datetime.utcnow()
            task.parsed_results = [{
                "tool": task.tool_id,
                "title": "Tool execution failed",
                "severity": "MEDIUM",
                "evidence": result.get("stderr", ""),
            }]
            return task

        raw_records = adapter.parse_output(task.stdout or task.stderr or "")
        task.parsed_results = [adapter.normalize(rec) for rec in raw_records if isinstance(rec, dict)] or [{
            "tool": task.tool_id,
            "title": "No findings produced",
            "severity": "INFO",
            "evidence": task.stdout[:200] if task.stdout else "no output",
        }]
        task.status = "SUCCESS"
        task.ended_at = datetime.utcnow()
        return task


orchestrator = ToolOrchestrator()
