from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FindingBase(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    severity: str = "MEDIUM"
    cvss: float | None = None
    cwe: str | None = None
    asset: str | None = None
    ip: str | None = None
    hostname: str | None = None
    url: str | None = None
    port: int | None = None
    protocol: str | None = None
    service: str | None = None
    source_tool: str | None = None
    validation_status: str = "UNVERIFIED"
    confidence: float = 0.0
    exploitability: str | None = None
    exposure: str | None = None
    business_impact: str | None = None
    risk_score: int = 0
    priority: str = "MEDIUM"
    status: str = "OPEN"
    evidence: list[str] = Field(default_factory=list)
    remediation: str | None = None


class FindingCreate(FindingBase):
    pass


class Finding(FindingBase):
    finding_id: str
    assessment_id: str
    asset_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
