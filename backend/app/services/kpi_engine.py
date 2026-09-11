from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class KPIRecord:
    metric: str
    value: float
    unit: str
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "value": self.value,
            "unit": self.unit,
            "updated_at": self.updated_at.isoformat(),
        }


class KPIEngine:
    def __init__(self) -> None:
        self._records = {
            "mttd_hours": KPIRecord("mttd_hours", 18.4, "hours"),
            "mttr_hours": KPIRecord("mttr_hours", 9.2, "hours"),
            "closure_rate_percent": KPIRecord("closure_rate_percent", 72.5, "%"),
            "risk_reduction_percent": KPIRecord("risk_reduction_percent", 47.2, "%"),
            "open_findings": KPIRecord("open_findings", 24.0, "count"),
            "critical_findings": KPIRecord("critical_findings", 4.0, "count"),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "mttd_hours": self._records["mttd_hours"].value,
            "mttr_hours": self._records["mttr_hours"].value,
            "closure_rate_percent": self._records["closure_rate_percent"].value,
            "risk_reduction_percent": self._records["risk_reduction_percent"].value,
            "open_findings": self._records["open_findings"].value,
            "critical_findings": self._records["critical_findings"].value,
        }


kpi_engine = KPIEngine()
