from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from app.adapters.base import SecurityToolAdapter


class NucleiAdapter(SecurityToolAdapter):
    name = "nuclei"
    version = "unknown"

    def detect(self) -> bool:
        return shutil.which("nuclei") is not None

    def validate(self) -> bool:
        return self.detect()

    def build_command(self, target: str, options: dict[str, Any] | None = None) -> list[str]:
        cmd = ["nuclei", "-target", target]
        if options:
            if options.get("severity"):
                cmd.extend(["-severity", str(options["severity"])])
            if options.get("json"):
                cmd.append("-json")
        return cmd

    def execute(self, target: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        command = self.build_command(target, options)
        if not self.detect():
            return {
                "command": command,
                "returncode": 127,
                "stdout": "",
                "stderr": "nuclei is not installed or not available on PATH",
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
                "stderr": "nuclei is not installed or not available on PATH",
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
        items: list[dict[str, Any]] = []
        for line in raw_output.splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                items.append(payload)
        return items

    def normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "tool": "nuclei",
            "title": record.get("info", {}).get("name") or "Template match",
            "severity": record.get("info", {}).get("severity", "UNKNOWN").upper(),
            "evidence": record.get("matched-at") or record.get("template-id") or "",
            "confidence": 0.88,
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.detect(),
            "version": self.version,
            "status": "ok" if self.detect() else "missing",
        }
