from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class RemediationTask:
    task_id: str
    title: str
    description: str
    priority: str
    assignee: str
    status: str = "OPEN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "assignee": self.assignee,
            "status": self.status,
        }


@dataclass
class RemediationPlan:
    plan_id: str
    assessment_id: str
    finding_ids: list[str]
    assignee: str
    status: str = "OPEN"
    created_at: datetime = field(default_factory=datetime.utcnow)
    tasks: list[RemediationTask] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "assessment_id": self.assessment_id,
            "finding_ids": self.finding_ids,
            "assignee": self.assignee,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "tasks": [task.to_dict() for task in self.tasks],
        }


class RemediationEngine:
    def __init__(self) -> None:
        self._plans: list[RemediationPlan] = []

    def generate(self, assessment_id: str, finding_ids: list[str], assignee: str = "security-team") -> RemediationPlan:
        plan = RemediationPlan(
            plan_id=f"R-{len(self._plans) + 1:03d}",
            assessment_id=assessment_id,
            finding_ids=finding_ids,
            assignee=assignee,
        )
        for index, finding_id in enumerate(finding_ids, start=1):
            priority = "HIGH" if index == 1 else "MEDIUM"
            plan.tasks.append(
                RemediationTask(
                    task_id=f"RT-{len(plan.tasks) + 1:03d}",
                    title=f"Remediate finding {finding_id}",
                    description=f"Apply a validated remediation for {finding_id} and confirm the fix with evidence.",
                    priority=priority,
                    assignee=assignee,
                )
            )
        self._plans.append(plan)
        return plan

    def list_plans(self) -> list[dict[str, Any]]:
        return [plan.to_dict() for plan in self._plans]


remediation_engine = RemediationEngine()
