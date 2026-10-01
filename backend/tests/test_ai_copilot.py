from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.api.deps import get_current_user
from app.core.database import Base, get_db
from app.main import app
from app.models.assessment import Assessment
from app.models.finding import Finding


def test_ai_uses_persisted_evidence_and_never_executes_actions() -> None:
    engine = create_engine("sqlite://", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    db = session_factory()
    db.add(Assessment(id="ai-assessment", name="AI evidence test", status="AUTHORIZED", is_authorized=True))
    db.add(Finding(
        finding_id="F-AI-001", assessment_id="ai-assessment", title="Critical remote code execution",
        severity="CRITICAL", risk_score=96, confidence=0.94, asset="api.example.com",
        source_tool="nuclei", validation_status="UNVERIFIED", evidence='["template matched response"]',
    ))
    db.commit()
    db.close()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="admin"), disabled=False)
    try:
        response = TestClient(app).post("/api/ai/ask", json={"prompt": "What is the most dangerous finding?", "assessment_id": "ai-assessment"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["classification"] == "EVIDENCE_SUMMARY"
        assert body["read_only"] is True
        assert body["actions_executed"] == []
        assert body["evidence_count"] == 1
        assert body["evidence"][0]["finding_id"] == "F-AI-001"
        assert "F-AI-001" in body["answer"]
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
