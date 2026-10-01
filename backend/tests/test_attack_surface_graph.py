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
from app.models.assessment import Assessment, AssessmentScope
from app.models.finding import Finding
from app.models.target import Target


def test_attack_surface_graph_contains_only_explicit_assessment_target_service_finding_edges() -> None:
    engine = create_engine("sqlite://", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    db = session_factory()
    db.add(Assessment(id="graph-assessment", name="Graph scope", is_authorized=True, status="AUTHORIZED"))
    db.add(AssessmentScope(id="scope-1", assessment_id="graph-assessment", target="api.example.com", kind="domain", allowed=True))
    db.add(Finding(
        finding_id="F-GRAPH-1", assessment_id="graph-assessment", title="TLS issue",
        severity="HIGH", risk_score=78, asset="api.example.com", port=443,
        protocol="tcp", service="https", source_tool="nmap", evidence='["443/tcp open"]',
    ))
    db.commit(); db.close()

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
        response = client.get("/api/targets/graph", params={"assessment_id": "graph-assessment"})
        assert response.status_code == 200, response.text
        graph = response.json()
        nodes = {node["data"]["id"]: node["data"] for node in graph["elements"]["nodes"]}
        edges = [edge["data"] for edge in graph["elements"]["edges"]]
        assert nodes["assessment:graph-assessment"]["kind"] == "assessment"
        target_id = next(node_id for node_id, node in nodes.items() if node["kind"] == "target")
        finding_id = "finding:F-GRAPH-1"
        service_id = next(node_id for node_id, node in nodes.items() if node["kind"] == "service")
        assert any(edge["source"] == "assessment:graph-assessment" and edge["target"] == target_id and edge["relation"] == "allows" for edge in edges)
        assert any(edge["source"] == target_id and edge["target"] == finding_id and edge["relation"] == "observed finding" for edge in edges)
        assert any(edge["source"] == target_id and edge["target"] == service_id and edge["relation"] == "observed service" for edge in edges)
        assert any(edge["source"] == service_id and edge["target"] == finding_id and edge["relation"] == "associated finding" for edge in edges)

        filtered = client.get("/api/targets/graph", params={"assessment_id": "graph-assessment", "q": "api.example.com"})
        assert filtered.status_code == 200
        assert filtered.json()["counts"]["nodes"] >= 3
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
