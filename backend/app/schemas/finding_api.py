from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, Field


class AssetRef(BaseModel):
    id: str
    name: Optional[str]
    business_unit: Optional[str]
    tags: List[str] = Field(default_factory=list)


class Observation(BaseModel):
    obs_id: str
    tool: str
    tool_version: Optional[str] = None
    assessment_id: Optional[str] = None
    asset: Optional[AssetRef] = None
    raw_output_url: Optional[str] = None
    parsed: Optional[dict] = None
    timestamp: datetime
    trust: Optional[str] = "TOOL_OBSERVED"
    meta: Optional[dict] = None


class Correlation(BaseModel):
    correlation_id: Optional[str]
    score: Optional[float]
    rules: List[str] = Field(default_factory=list)
    merged_from: List[str] = Field(default_factory=list)


class RemediationRef(BaseModel):
    remediation_id: Optional[str]
    status: Optional[str]
    expected_risk_reduction: Optional[float]
    effort_estimate: Optional[str]


class RetestHistoryItem(BaseModel):
    id: str
    status: str
    timestamp: datetime
    evidence: List[str] = Field(default_factory=list)


class AuditEvent(BaseModel):
    event: str
    actor: Optional[str]
    timestamp: datetime
    details: Optional[dict]


class FindingFull(BaseModel):
    finding_id: str
    title: str
    description: Optional[str] = None
    severity: str
    risk_score: Optional[float] = 0.0
    confidence: Optional[int] = 0
    trust: Optional[str] = "CORRELATED"
    asset: AssetRef
    attack_vector: Optional[str] = None
    cves: List[dict] = Field(default_factory=list)
    cwe: List[str] = Field(default_factory=list)
    cvss: Optional[float] = None
    exploitability: Optional[str] = None
    status: Optional[str] = "OPEN"
    owner: Optional[dict] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    sources: List[Observation] = Field(default_factory=list)
    correlation: Optional[Correlation] = None
    remediation: Optional[RemediationRef] = None
    retest: Optional[dict] = None
    audit: List[AuditEvent] = Field(default_factory=list)

    class Config:
        orm_mode = True


class FindingsListResponse(BaseModel):
    items: List[FindingFull] = Field(default_factory=list)
    page: dict = Field(default_factory=lambda: {"page": 1, "size": 25, "total": 0})
