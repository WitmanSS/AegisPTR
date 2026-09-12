"""Run pytest (via current Python) and save stdout/stderr to backend/test_output.txt.
This version is defensive: it uses the current interpreter, captures stdout/stderr,
records returncode, timestamps, and writes any exceptions to the output file.

Usage: python backend/scripts/collect_pytest_output.py
"""
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "test_output.txt"

def main():
    # Use the same python executable that's running this script to invoke pytest
    py = sys.executable
    cmd = [py, "-m", "pytest", "-q", "-r", "a", "-s"]
    env = os.environ.copy()
    # ensure repo root is on PYTHONPATH so package imports work
    env["PYTHONPATH"] = str(Path.cwd())

    start = datetime.utcnow()
    try:
        res = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=900)
        end = datetime.utcnow()
        with OUT.open("w", encoding="utf-8") as fh:
            fh.write(f"Command: {' '.join(cmd)}\n")
            fh.write(f"Started: {start.isoformat()}Z\nEnded: {end.isoformat()}Z\n\n")
            fh.write("--- STDOUT ---\n")
            fh.write(res.stdout or "")
            fh.write("\n--- STDERR ---\n")
            fh.write(res.stderr or "")
            fh.write(f"\nReturn code: {res.returncode}\n")
    except Exception as exc:  # pragma: no cover - operational helper
        end = datetime.utcnow()
        with OUT.open("w", encoding="utf-8") as fh:
            fh.write(f"Command: {' '.join(cmd)}\n")
            fh.write(f"Started: {start.isoformat()}Z\nException at: {end.isoformat()}Z\n\n")
            fh.write("Exception:\n")
            fh.write(traceback.format_exc())

    print(f"Saved pytest output to {OUT}")


if __name__ == "__main__":
    main()
