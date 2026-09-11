import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import app.core.database as db_module
from app.core.database import Base, get_db
from app.main import app


def test_assessment_api_create_and_list() -> None:
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

        create_response = client.post(
            "/api/assessments",
            json={
                "name": "Sandbox Assessment",
                "client": "Contoso",
                "assessment_type": "External",
                "scope": ["203.0.113.10/32", "example.com"],
                "exclusions": ["203.0.113.10"],
                "status": "DRAFT",
            },
        )

        assert create_response.status_code == 200, create_response.text
        payload = create_response.json()
        assert payload["name"] == "Sandbox Assessment"
        assert payload["client"] == "Contoso"

        list_response = client.get("/api/assessments")
        assert list_response.status_code == 200
        items = list_response.json()
        assert any(item["name"] == "Sandbox Assessment" for item in items)

        auth_response = client.post(
            f"/api/assessments/{payload['id']}/authorize",
            json={"authorized": True},
        )
        assert auth_response.status_code == 200
        assert auth_response.json()["is_authorized"] is True
        assert auth_response.json()["status"] == "AUTHORIZED"

        task_response = client.post(
            "/api/tasks",
            json={
                "assessment_id": payload["id"],
                "tool_id": "nmap",
                "target": "example.com",
                "options": {"scan_type": "quick"},
            },
        )
        assert task_response.status_code == 200
        task_payload = task_response.json()
        assert task_payload["status"] == "QUEUED"
        assert task_payload["tool_id"] == "nmap"

        execute_response = client.post(f"/api/tasks/{task_payload['task_id']}/execute")
        assert execute_response.status_code == 200
        run_payload = execute_response.json()
        assert run_payload["status"] in {"SUCCESS", "SKIPPED"}
        assert len(run_payload["parsed_results"]) >= 1

        ingest_response = client.post(
            "/api/findings/ingest",
            json={
                "assessment_id": payload["id"],
                "findings": [
                    {
                        "title": "Open service on example.com",
                        "description": "Service reachable over HTTP",
                        "severity": "HIGH",
                        "risk_score": 78,
                        "asset": "example.com",
                        "source_tool": "nmap",
                        "evidence": ["open port 80/tcp"],
                        "status": "OPEN",
                    }
                ],
            },
        )
        assert ingest_response.status_code == 200
        assert len(ingest_response.json()["saved"]) == 1

        findings_response = client.get("/api/findings")
        assert findings_response.status_code == 200
        assert any(item["title"] == "Open service on example.com" for item in findings_response.json())

        reports_response = client.get("/api/reports/summary")
        assert reports_response.status_code == 200
        summary = reports_response.json()
        assert "prioritized_findings" in summary
        assert isinstance(summary["prioritized_findings"], list)
    finally:
        app.dependency_overrides.clear()
