import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app


def test_kpi_dashboard_summary() -> None:
    client = TestClient(app)
    response = client.get("/api/monitoring/summary")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "mttd_hours" in payload
    assert "mttr_hours" in payload
    assert "closure_rate_percent" in payload
    assert "risk_reduction_percent" in payload
    assert payload["status"] == "ok"
