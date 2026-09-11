from __future__ import annotations

import shutil
import subprocess
from typing import Any

from app.adapters.base import SecurityToolAdapter


class NmapAdapter(SecurityToolAdapter):
    name = "nmap"
    version = "unknown"

    def detect(self) -> bool:
        return shutil.which("nmap") is not None

    def validate(self) -> bool:
        return self.detect()

    def build_command(self, target: str, options: dict[str, Any] | None = None) -> list[str]:
        cmd = ["nmap"]
        if options:
            if options.get("fast"):
                cmd.append("-F")
            if options.get("top_ports"):
                cmd.extend(["--top-ports", str(options["top_ports"])])
            if options.get("service_detection"):
                cmd.append("-sV")
            if options.get("os_detection"):
                cmd.append("-O")
        cmd.append(target)
        return cmd

    def execute(self, target: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        command = self.build_command(target, options)
        if not self.detect():
            return {
                "command": command,
                "returncode": 127,
                "stdout": "",
                "stderr": "nmap is not installed or not available on PATH",
                "success": False,
            }
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
        except FileNotFoundError:
            return {
                "command": command,
                "returncode": 127,
                "stdout": "",
                "stderr": "nmap is not installed or not available on PATH",
                "success": False,
            }
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "success": completed.returncode == 0,
        }

    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        findings: list[dict[str, Any]] = []
        for line in lines:
            if line.startswith("Nmap scan report for") or line.startswith("PORT"):
                continue
            if "/tcp" in line or "/udp" in line:
                findings.append({"raw": line})
        return findings

    def normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "nmap",
            "title": "Network service detected",
            "evidence": record.get("raw", ""),
            "confidence": 0.9,
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.detect(),
            "version": self.version,
            "status": "ok" if self.detect() else "missing",
        }
