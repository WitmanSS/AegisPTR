from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentScopeCreate(BaseModel):
    target: str
    kind: str = "cidr"
    allowed: bool = True


class AssessmentCreate(BaseModel):
    name: str
    client: str | None = None
    assessment_type: str = "External"
    scope: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    status: str = "DRAFT"


class AssessmentRead(BaseModel):
    id: str
    name: str
    client: str | None = None
    assessment_type: str
    status: str
    scope_text: str | None = None
    exclusions: str | None = None
    is_authorized: bool = False
    created_at: datetime
    updated_at: datetime
