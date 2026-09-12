from __future__ import annotations

import ipaddress
import re
import socket
from typing import List, Dict, Any
from urllib.parse import urlparse


RANGE_RE = re.compile(r"^(?P<start>\d+\.\d+\.\d+\.\d+)-(?P<end>\d+\.\d+\.\d+\.\d+)$")


def detect_target_type(value: str) -> str:
    v = value.strip()
    # URL
    if "://" in v:
        return "url"
    # CIDR
    try:
        ipaddress.ip_network(v, strict=False)
        return "cidr_or_ip"
    except Exception:
        pass
    # Range
    if RANGE_RE.match(v):
        return "ip_range"
    # IPv4/IPv6 single
    try:
        ipaddress.ip_address(v)
        return "ip"
    except Exception:
        pass
    # port-specific (host:port)
    if ":" in v and not v.startswith("http"):
        host, sep, port = v.rpartition(":")
        if port.isdigit():
            return "host_port"
    # domain/hostname
    if re.match(r"^[A-Za-z0-9.-]+$", v):
        if "." in v:
            return "domain_or_hostname"
    return "unknown"


def normalize_target(value: str) -> Dict[str, Any]:
    v = value.strip()
    t = detect_target_type(v)
    result = {"original": v, "canonical": v, "type": t}
    if t == "url":
        p = urlparse(v)
        canonical = p.geturl().rstrip("/")
        result.update({"canonical": canonical, "protocol": p.scheme, "hostname": p.hostname, "port": p.port, "path": p.path})
    elif t == "cidr_or_ip":
        try:
            net = ipaddress.ip_network(v, strict=False)
            result.update({"canonical": str(net), "network": str(net)})
        except Exception:
            pass
    elif t == "ip_range":
        m = RANGE_RE.match(v)
        if m:
            result.update({"start": m.group("start"), "end": m.group("end")})
    elif t == "ip":
        result.update({"canonical": v})
    elif t == "domain_or_hostname":
        result.update({"canonical": v.lower()})
    return result


def validate_target(value: str, resolve: bool = False) -> Dict[str, Any]:
    out = {"original": value, "valid": False, "errors": [], "type": None}
    t = detect_target_type(value)
    out["type"] = t
    try:
        if t == "ip":
            ipaddress.ip_address(value)
            out["valid"] = True
        elif t == "cidr_or_ip":
            ipaddress.ip_network(value, strict=False)
            out["valid"] = True
        elif t == "ip_range":
            m = RANGE_RE.match(value)
            if not m:
                out["errors"].append("invalid range")
            else:
                out["valid"] = True
        elif t == "url":
            p = urlparse(value)
            if not p.scheme or not p.netloc:
                out["errors"].append("invalid url")
            else:
                out["valid"] = True
        elif t == "domain_or_hostname":
            if not re.match(r"^[A-Za-z0-9.-]+$", value):
                out["errors"].append("invalid domain/hostname")
            else:
                out["valid"] = True
        else:
            out["errors"].append("unknown target type")
    except Exception as e:
        out["errors"].append(str(e))

    if resolve and out.get("valid") and out.get("type") in ("domain_or_hostname", "url"):
        host = urlparse(value).hostname if out.get("type") == "url" else value
        try:
            addrs = socket.getaddrinfo(host, None)
            out["resolved"] = list({ai[4][0] for ai in addrs if ai and ai[4]})
        except Exception as e:
            out["resolved_error"] = str(e)

    return out


def parse_bulk(text: str) -> Dict[str, Any]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    parsed = []
    seen = set()
    for line in lines:
        n = normalize_target(line)
        can = n.get("canonical") or n.get("original")
        if can in seen:
            parsed.append({"original": line, "status": "duplicate"})
            continue
        seen.add(can)
        validation = validate_target(line)
        parsed.append({"original": line, "canonical": n.get("canonical"), "type": n.get("type"), "validation": validation})

    # basic CIDR overlap detection (naive)
    cidrs = [p["canonical"] for p in parsed if p.get("type") == "cidr_or_ip"]
    overlaps = []
    try:
        nets = [ipaddress.ip_network(c) for c in cidrs]
        for i, a in enumerate(nets):
            for b in nets[i + 1:]:
                if a.overlaps(b):
                    overlaps.append((str(a), str(b)))
    except Exception:
        pass

    return {"count": len(parsed), "items": parsed, "overlaps": overlaps}
