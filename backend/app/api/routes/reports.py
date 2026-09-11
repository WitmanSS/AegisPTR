from __future__ import annotations

from fastapi import APIRouter

from app.services.risk_engine import risk_engine

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
async def report_summary() -> dict:
    findings = [
        {"title": "Open SSH", "severity": "HIGH", "risk_score": 88, "asset": "host-01", "evidence": ["22/tcp open"]},
        {"title": "Open SSH", "severity": "HIGH", "risk_score": 82, "asset": "host-01", "evidence": ["22/tcp open"]},
        {"title": "Missing TLS", "severity": "MEDIUM", "risk_score": 54, "asset": "api.local", "evidence": ["TLS 1.0"]},
    ]
    correlated = risk_engine.correlate_findings(findings)
    return {
        "assessment": "AegisPTR assessment",
        "risk_reduction": "47.2%",
        "critical_findings": sum(1 for item in correlated if item["priority"] == "CRITICAL"),
        "high_findings": sum(1 for item in correlated if item["priority"] == "HIGH"),
        "prioritized_findings": correlated,
    }
