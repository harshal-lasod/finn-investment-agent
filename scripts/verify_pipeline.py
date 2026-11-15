"""Run the project's focused backend integration checks."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
result = subprocess.run(
    [sys.executable, "-m", "pytest", "backend/tests", "-q"],
    cwd=ROOT,
    check=False,
)
raise SystemExit(result.returncode)
