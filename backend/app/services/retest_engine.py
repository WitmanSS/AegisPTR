from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RetestRecord:
    retest_id: str
    assessment_id: str
    finding_id: str
    retest_type: str
    status: str = "PENDING"
    passed: bool | None = None
    evidence: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "retest_id": self.retest_id,
            "assessment_id": self.assessment_id,
            "finding_id": self.finding_id,
            "retest_type": self.retest_type,
            "status": self.status,
            "passed": self.passed,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RetestEngine:
    def __init__(self) -> None:
        self._records: list[RetestRecord] = []

    def create(self, assessment_id: str, finding_id: str, retest_type: str, status: str = "PENDING") -> RetestRecord:
        record = RetestRecord(
            retest_id=f"RT-{len(self._records) + 1:03d}",
            assessment_id=assessment_id,
            finding_id=finding_id,
            retest_type=retest_type,
            status=status,
        )
        self._records.append(record)
        return record

    def validate(self, retest_id: str, passed: bool, evidence: list[str] | None = None) -> RetestRecord:
        for record in self._records:
            if record.retest_id == retest_id:
                record.passed = passed
                record.evidence = evidence or []
                record.status = "PASSED" if passed else "FAILED"
                record.updated_at = datetime.utcnow()
                return record
        raise KeyError(f"Retest record {retest_id} not found")

    def list_records(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self._records]


retest_engine = RetestEngine()
