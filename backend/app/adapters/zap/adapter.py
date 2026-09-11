from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from app.adapters.base import SecurityToolAdapter


class ZAPAdapter(SecurityToolAdapter):
    name = "zap"
    version = "unknown"

    def detect(self) -> bool:
        return shutil.which("zaproxy") is not None or shutil.which("zap-cli") is not None

    def validate(self) -> bool:
        return self.detect()

    def build_command(self, target: str, options: dict[str, Any] | None = None) -> list[str]:
        cmd = ["zap-cli", "quick-scan", "-s", "xss,sqli", target]
        if options:
            if options.get("target"):
                cmd[-1] = str(options["target"])
        return cmd

    def execute(self, target: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        command = self.build_command(target, options)
        if not self.detect():
            return {
                "command": command,
                "returncode": 127,
                "stdout": "",
                "stderr": "zap is not installed or not available on PATH",
                "success": False,
            }
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
        except FileNotFoundError:
            return {
                "command": command,
                "returncode": 127,
                "stdout": "",
                "stderr": "zap is not installed or not available on PATH",
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
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError:
            return [{"raw": raw_output}]
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            return [payload]
        return []

    def normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "tool": "zap",
            "title": record.get("alert", "Web issue found"),
            "severity": record.get("risk", "INFO").upper(),
            "evidence": record.get("description", ""),
            "confidence": 0.8,
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.detect(),
            "version": self.version,
            "status": "ok" if self.detect() else "missing",
        }
