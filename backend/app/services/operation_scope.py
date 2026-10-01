from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from app.models.assessment import Assessment


def _is_ip_in_network(target: str, network_value: str) -> bool:
    try:
        address = ipaddress.ip_address(target)
        network = ipaddress.ip_network(network_value, strict=False)
    except ValueError:
        return False
    return address in network


def is_target_authorized(assessment: Assessment, target: str) -> bool:
    normalized_target = target.strip().rstrip("/").lower()
    if not assessment.is_authorized or not normalized_target:
        return False

    allowed = [item.strip().rstrip("/").lower() for item in (assessment.scope_text or "").split(";") if item.strip()]
    excluded = [item.strip().rstrip("/").lower() for item in (assessment.exclusions or "").split(";") if item.strip()]

    host = urlsplit(normalized_target).hostname
    target_parts = {normalized_target}
    if host:
        target_parts.add(host.lower())
    if any(part in excluded or any(_is_ip_in_network(part, item) for item in excluded) for part in target_parts):
        return False
    if normalized_target in allowed:
        return True

    if host and host in allowed:
        return True
    return any(_is_ip_in_network(normalized_target, item) for item in allowed)
