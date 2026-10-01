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


def test_ingest_persists_findings_and_correlates_independent_tools() -> None:
    engine = create_engine("sqlite://", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    db = session_factory()
    db.add(Assessment(id="findings-assessment", name="Findings test", status="AUTHORIZED", is_authorized=True))
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
        client = TestClient(app)
        ingested = client.post("/api/findings/ingest", json={
            "assessment_id": "findings-assessment",
            "findings": [
                {"title": "Outdated package allows remote code execution", "severity": "HIGH", "risk_score": 76, "confidence": 0.9, "asset": "api.example.com", "cve": "CVE-2025-1234", "source_tool": "nuclei", "evidence": ["template matched"]},
                {"title": "Remote code execution in dependency", "severity": "CRITICAL", "risk_score": 92, "confidence": 0.95, "asset": "API.EXAMPLE.COM", "cve": "CVE-2025-1234", "source_tool": "zap", "evidence": ["active check confirmed"]},
            ],
        })
        assert ingested.status_code == 200, ingested.text
        saved = ingested.json()["saved"]
        assert len(saved) == 2
        assert saved[0]["finding_id"] != saved[1]["finding_id"]

        listing = client.get("/api/findings/explorer", params={"severity": "CRITICAL", "assessment_id": "findings-assessment"})
        assert listing.status_code == 200
        assert listing.json()["page"]["total"] == 1
        assert listing.json()["items"][0]["cve"] == "CVE-2025-1234"

        correlations = client.get("/api/findings/correlations", params={"assessment_id": "findings-assessment"})
        assert correlations.status_code == 200
        group = correlations.json()["items"][0]
        assert group["observation_count"] == 2
        assert group["source_tools"] == ["nuclei", "zap"]
        assert "same assessment" in group["rules"]
        assert len(group["evidence"]) == 2

        updated = client.post(f"/api/findings/{saved[0]['finding_id']}/actions", json={"action": "set_status", "status": "TRIAGED"})
        assert updated.status_code == 200
        assert updated.json()["finding"]["status"] == "TRIAGED"
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
