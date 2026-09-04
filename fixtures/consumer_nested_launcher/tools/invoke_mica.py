"""Thin consumer launcher for a released MICA checkout."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    mica_root = os.environ.get("MICA_ROOT")
    if not mica_root:
        print("MICA_ROOT must name a released MICA checkout", file=sys.stderr)
        return 2

    project_root = Path(__file__).resolve().parents[1]
    runtime = Path(mica_root).resolve() / "tools" / "mica_runtime.py"
    if not runtime.is_file():
        print(f"MICA runtime not found: {runtime}", file=sys.stderr)
        return 2

    completed = subprocess.run(
        [sys.executable, str(runtime), str(project_root), *sys.argv[1:]],
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
