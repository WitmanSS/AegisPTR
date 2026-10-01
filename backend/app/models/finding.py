from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    finding_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, default=lambda: str(uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cve: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    cwe: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cvss: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), default="MEDIUM")
    asset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    service: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_tool: Mapped[str | None] = mapped_column(String(255), nullable=True)
    validation_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED")
    confidence: Mapped[float] = mapped_column(Float, default=0)
    exploitability: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exposure: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    evidence: Mapped[str] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
