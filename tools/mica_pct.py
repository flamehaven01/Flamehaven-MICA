#!/usr/bin/env python3
"""
MICA PCT Validator v0.2.6 -- portable self-diagnostic runner.

Delegates all PCT judgment to mica_core.run_pct_checks().
In v0.2.4 and earlier, mica_pct.py contained its own PCT logic and
mica_runtime.py contained a separate shallow pct_status() check that could
disagree with it. v0.2.5 centralizes judgment in mica_core.py so both tools
always agree on package state.

v0.2.6: PCT-010 escalates from WARN to FAIL when mica.yaml sets
di_policy.critical_binding_required: true.

Usage:
    python mica_pct.py [project_root]

Exit code: 0 = CLOSED CONTRACT, 1 = INCOMPLETE/FAILURE
"""

from __future__ import annotations

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from mica_core import is_closed_contract, run_pct_checks


def _report(results: list[tuple[str, str, str]]) -> bool:
    print()
    for pid, status, msg in results:
        print(f"{pid} [{status:<4}] {msg}")
    print()
    closed = is_closed_contract(results)
    print("Overall:", "CLOSED CONTRACT" if closed else "INCOMPLETE")
    print()
    return closed


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    if not root.is_dir():
        print(f"[ERROR] Not a directory: {root}")
        sys.exit(1)
    print("MICA PCT Validator v0.2.6")
    print(f"Project root: {root}")
    results = run_pct_checks(root)
    closed = _report(results)
    sys.exit(0 if closed else 1)


if __name__ == "__main__":
    main()
