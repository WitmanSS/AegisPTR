from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Any, Dict


class TargetBase(BaseModel):
    original: str
    canonical: str | None = None
    target_type: str | None = None
    protocol: str | None = None
    hostname: str | None = None
    ip: str | None = None
    port: int | None = None
    path: str | None = None
    environment: str | None = None
    business_unit: str | None = None
    criticality: str | None = None
    owner: str | None = None
    authorization_status: str | None = None
    scope_status: str | None = None
    tags: List[str] = Field(default_factory=list)
    notes: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class TargetCreate(TargetBase):
    pass


class TargetOut(TargetBase):
    id: str
    created_at: datetime
    updated_at: datetime


class BulkParseRequest(BaseModel):
    text: str
    resolve: bool = False


class BulkParseItem(BaseModel):
    original: str
    canonical: str | None = None
    type: str | None = None
    validation: Dict[str, Any] | None = None


class BulkParseResponse(BaseModel):
    count: int
    items: List[BulkParseItem]
    overlaps: List[List[str]]


class BulkCreateRequest(BaseModel):
    items: List[TargetCreate]


class BulkCreateResultItem(BaseModel):
    original: str
    id: str | None = None
    status: str
    error: str | None = None


class BulkCreateResponse(BaseModel):
    total: int
    created: int
    failed: int
    items: List[BulkCreateResultItem]
