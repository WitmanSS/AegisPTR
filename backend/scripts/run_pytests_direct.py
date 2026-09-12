"""Run pytest.main() in-process and write output to backend/test_output.txt.
This helps capture pytest output even when subprocess execution doesn't surface logs.
Usage: python backend/scripts/run_pytests_direct.py
"""
import sys
from pathlib import Path
from datetime import datetime
import traceback
import pytest
from contextlib import redirect_stdout, redirect_stderr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "test_output.txt"

def main():
    start = datetime.utcnow()
    try:
        with OUT.open("w", encoding="utf-8") as fh:
            fh.write(f"Started: {start.isoformat()}Z\n\n")
            with redirect_stdout(fh), redirect_stderr(fh):
                # Run pytest with -q -r a -s
                ret = pytest.main(["-q", "-r", "a", "-s"])
            fh.write(f"\nReturn code: {ret}\n")
    except Exception:
        with OUT.open("a", encoding="utf-8") as fh:
            fh.write("\nException:\n")
            fh.write(traceback.format_exc())
    print(f"Saved pytest output to {OUT}")

if __name__ == "__main__":
    main()
