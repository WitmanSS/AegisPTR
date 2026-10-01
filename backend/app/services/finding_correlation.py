from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any

SEVERITY_RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _asset_key(finding: dict[str, Any]) -> str:
    return _normalize(finding.get("asset") or finding.get("hostname") or finding.get("ip") or finding.get("url")) or "unknown"


def _identity_key(finding: dict[str, Any]) -> tuple[str, str]:
    cve = _normalize(finding.get("cve"))
    if cve:
        return "cve", cve
    return "title", _normalize(finding.get("title"))


def correlate_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group observations only when the assessment, asset, and issue fingerprint match."""
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        assessment_id = str(finding.get("assessment_id") or "")
        asset = _asset_key(finding)
        identity_type, identity = _identity_key(finding)
        if assessment_id and identity:
            grouped[(assessment_id, asset, identity_type, identity)].append(finding)

    correlations: list[dict[str, Any]] = []
    for key, observations in grouped.items():
        if len(observations) < 2:
            continue
        assessment_id, asset, identity_type, identity = key
        unique_tools = sorted({str(item.get("source_tool") or "unknown").strip().lower() for item in observations})
        highest = max(observations, key=lambda item: SEVERITY_RANK.get(str(item.get("severity", "MEDIUM")).upper(), 2))
        scores = [int(item.get("risk_score") or 0) for item in observations]
        evidence = []
        for observation in observations:
            source = observation.get("source_tool") or "unknown tool"
            values = observation.get("evidence") or []
            if isinstance(values, str):
                values = [values]
            for value in values:
                evidence.append({"source_tool": source, "finding_id": observation.get("finding_id"), "value": value})
        digest = hashlib.sha256("|".join(key).encode("utf-8")).hexdigest()[:16]
        rules = ["same assessment", "same normalized asset", "same vulnerability fingerprint" if identity_type == "cve" else "same normalized title"]
        confidence = min(0.99, 0.75 + 0.08 * max(len(unique_tools) - 1, 0) + 0.02 * max(len(observations) - len(unique_tools), 0))
        correlations.append({
            "correlation_id": f"COR-{digest}",
            "assessment_id": assessment_id,
            "asset": asset,
            "fingerprint": {"type": identity_type, "value": identity},
            "title": highest.get("title"),
            "severity": str(highest.get("severity", "MEDIUM")).upper(),
            "risk_score": max(scores, default=0),
            "confidence": round(confidence, 2),
            "observation_count": len(observations),
            "source_tools": unique_tools,
            "statuses": sorted({str(item.get("status", "OPEN")).upper() for item in observations}),
            "merged_from": [item.get("finding_id") for item in observations],
            "rules": rules,
            "evidence": evidence,
        })
    return sorted(correlations, key=lambda item: (item["risk_score"], item["observation_count"]), reverse=True)
