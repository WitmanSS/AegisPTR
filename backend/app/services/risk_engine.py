from __future__ import annotations

from collections import defaultdict
from typing import Any

SEVERITY_WEIGHT = {
    "CRITICAL": 40,
    "HIGH": 25,
    "MEDIUM": 15,
    "LOW": 8,
    "INFO": 2,
}

PRIORITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


class RiskEngine:
    @staticmethod
    def normalize_severity(value: str | None) -> str:
        normalized = (value or "MEDIUM").upper()
        return normalized if normalized in SEVERITY_WEIGHT else "MEDIUM"

    @staticmethod
    def calculate_risk_score(finding: dict[str, Any]) -> int:
        severity = RiskEngine.normalize_severity(finding.get("severity"))
        base = SEVERITY_WEIGHT.get(severity, 15)
        confidence = float(finding.get("confidence", 0.8) or 0.8)
        score = int(base * confidence)
        if finding.get("risk_score") is not None:
            score = max(score, int(finding["risk_score"]))
        return min(score, 100)

    @staticmethod
    def determine_priority(score: int) -> str:
        if score >= 90:
            return "CRITICAL"
        if score >= 70:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        if score >= 20:
            return "LOW"
        return "INFO"

    @staticmethod
    def correlate_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for finding in findings:
            key = (finding.get("asset") or "unknown", finding.get("title") or "untitled")
            grouped[key].append(finding)

        correlated: list[dict[str, Any]] = []
        for group in grouped.values():
            merged = group[0].copy()
            merged["severity"] = max(
                (RiskEngine.normalize_severity(item.get("severity")) for item in group),
                key=lambda item: PRIORITY_ORDER.index(item) if item in PRIORITY_ORDER else 0,
            )
            merged["risk_score"] = max(RiskEngine.calculate_risk_score(item) for item in group)
            merged["priority"] = RiskEngine.determine_priority(merged["risk_score"])
            merged["evidence"] = list(
                {
                    evidence
                    for item in group
                    for evidence in item.get("evidence", [])
                }
            )
            correlated.append(merged)
        return sorted(correlated, key=lambda item: item.get("risk_score", 0), reverse=True)


risk_engine = RiskEngine()
