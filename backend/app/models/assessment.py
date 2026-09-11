from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assessment_type: Mapped[str] = mapped_column(String(50), default="External")
    status: Mapped[str] = mapped_column(String(50), default="DRAFT")
    scope_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusions: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False)


class AssessmentScope(Base):
    __tablename__ = "assessment_scopes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    assessment_id: Mapped[str] = mapped_column(String, nullable=False)
    target: Mapped[str] = mapped_column(String(512), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), default="cidr")
    allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
