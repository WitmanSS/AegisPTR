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
from app.services.orchestrator import orchestrator


def test_operation_create_and_execute_recheck_authorized_scope(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    db = session_factory()
    assessment = Assessment(
        id="operations-scope-test",
        name="Authorized test",
        status="AUTHORIZED",
        is_authorized=True,
        scope_text="example.com; 192.0.2.0/24",
        exclusions="192.0.2.9",
    )
    db.add(assessment)
    db.commit()
    assessment_id = assessment.id
    db.close()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="admin"), disabled=False)
    original_queues = {name: list(tasks) for name, tasks in orchestrator._queues.items()}

    async def fake_run(task):
        task.status = "SUCCESS"
        task.exit_code = 0
        task.parsed_results = [{"title": "test result"}]
        return task

    monkeypatch.setattr(orchestrator, "run", fake_run)
    try:
        client = TestClient(app)
        denied_assessment = client.post("/api/tasks", json={"assessment_id": "missing", "tool_id": "nmap", "target": "example.com"})
        assert denied_assessment.status_code == 404

        denied_target = client.post("/api/tasks", json={"assessment_id": assessment_id, "tool_id": "nmap", "target": "outside.example.net"})
        assert denied_target.status_code == 403

        created = client.post("/api/tasks", json={"assessment_id": assessment_id, "tool_id": "nmap", "target": "example.com"})
        assert created.status_code == 200, created.text
        task_id = created.json()["task_id"]

        db = session_factory()
        db_assessment = db.get(Assessment, assessment_id)
        db_assessment.is_authorized = False
        db_assessment.status = "DRAFT"
        db.commit()
        db.close()

        revoked = client.post(f"/api/tasks/{task_id}/execute")
        assert revoked.status_code == 403

        db = session_factory()
        db_assessment = db.get(Assessment, assessment_id)
        db_assessment.is_authorized = True
        db_assessment.status = "AUTHORIZED"
        db.commit()
        db.close()

        executed = client.post(f"/api/tasks/{task_id}/execute")
        assert executed.status_code == 200, executed.text
        assert executed.json()["status"] == "SUCCESS"
        assert executed.json()["parsed_results"] == [{"title": "test result"}]
    finally:
        app.dependency_overrides.clear()
        orchestrator._queues.clear()
        orchestrator._queues.update(original_queues)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
