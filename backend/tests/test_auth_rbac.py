import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app


def test_auth_rbac_flow() -> None:
    client = TestClient(app)

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "pentester",
            "password": "SecurePass123!",
            "role": "pentester",
        },
    )
    assert register_response.status_code == 200, register_response.text

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "pentester",
            "password": "SecurePass123!",
        },
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    assert token

    protected_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert protected_response.status_code == 200, protected_response.text
    assert protected_response.json()["username"] == "pentester"

    forbidden_response = client.get(
        "/api/admin/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert forbidden_response.status_code == 403, forbidden_response.text
