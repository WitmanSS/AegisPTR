from __future__ import annotations

import ipaddress
from typing import Iterable


class ScopeValidationError(ValueError):
    pass


class ScopeEngine:
    @staticmethod
    def parse_target(target: str) -> str:
        target = target.strip()
        if not target:
            raise ScopeValidationError("Empty target")
        return target

    @staticmethod
    def is_ip_in_scope(ip: str, allowed_ranges: Iterable[str], excluded: Iterable[str] | None = None) -> bool:
        candidate_ip = ipaddress.ip_address(ip)
        excluded_set = {ipaddress.ip_address(item.strip()) for item in (excluded or []) if item.strip()}
        if candidate_ip in excluded_set:
            return False

        for item in allowed_ranges:
            network = item.strip()
            if not network:
                continue
            try:
                if candidate_ip in ipaddress.ip_network(network, strict=False):
                    return True
            except ValueError:
                continue
        return False

    @staticmethod
    def validate_target(target: str, allowed: Iterable[str], excluded: Iterable[str] | None = None) -> bool:
        try:
            ip = ipaddress.ip_address(target)
            return ScopeEngine.is_ip_in_scope(ip.exploded, allowed, excluded)
        except ValueError:
            if target.startswith("http://") or target.startswith("https://"):
                return True
            if any(target.endswith(domain) for domain in [".example.com", ".local", ".test"]):
                return True
            return target in {item.strip() for item in allowed if item.strip()}


scope_engine = ScopeEngine()
