import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import Base, get_db
from app.main import app


def test_remediation_and_retest_workflow() -> None:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)

        assessment_response = client.post(
            "/api/assessments",
            json={
                "name": "Remediation Test",
                "client": "Contoso",
                "assessment_type": "External",
                "scope": ["203.0.113.20/32"],
                "exclusions": [],
                "status": "AUTHORIZED",
            },
        )
        assert assessment_response.status_code == 200, assessment_response.text
        assessment_id = assessment_response.json()["id"]

        client.post(
            f"/api/assessments/{assessment_id}/authorize",
            json={"authorized": True},
        )

        findings_response = client.post(
            "/api/findings/ingest",
            json={
                "assessment_id": assessment_id,
                "findings": [
                    {
                        "title": "Critical SQL Injection",
                        "description": "User input reaches database query",
                        "severity": "CRITICAL",
                        "risk_score": 96,
                        "asset": "app.contoso.local",
                        "source_tool": "nuclei",
                        "evidence": ["SQL injection payload reflected in response"],
                        "status": "OPEN",
                    }
                ],
            },
        )
        assert findings_response.status_code == 200, findings_response.text

        remediation_response = client.post(
            "/api/remediation/generate",
            json={
                "assessment_id": assessment_id,
                "finding_ids": ["F-001"],
                "assignee": "app-team",
            },
        )
        assert remediation_response.status_code == 200, remediation_response.text
        remediation_payload = remediation_response.json()
        assert remediation_payload["status"] == "OPEN"
        assert len(remediation_payload["tasks"]) >= 1

        plans_response = client.get("/api/remediation/plans")
        assert plans_response.status_code == 200
        assert isinstance(plans_response.json(), list)

        retest_response = client.post(
            "/api/retests",
            json={
                "assessment_id": assessment_id,
                "finding_id": "F-001",
                "retest_type": "POST_REMEDIATION",
                "status": "PENDING",
            },
        )
        assert retest_response.status_code == 200, retest_response.text
        retest_payload = retest_response.json()
        assert retest_payload["status"] == "PENDING"

        validate_response = client.post(
            f"/api/retests/{retest_payload['retest_id']}/validate",
            json={
                "passed": True,
                "evidence": ["No issue present after patch"],
            },
        )
        assert validate_response.status_code == 200, validate_response.text
        assert validate_response.json()["status"] == "PASSED"
    finally:
        app.dependency_overrides.clear()
