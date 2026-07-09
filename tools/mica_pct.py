#!/usr/bin/env python3
"""
MICA PCT Validator v0.2.8 -- portable self-diagnostic runner.

Delegates all PCT judgment to mica_core.run_pct_checks().
In v0.2.4 and earlier, mica_pct.py contained its own PCT logic and
mica_runtime.py contained a separate shallow pct_status() check that could
disagree with it. v0.2.5 centralizes judgment in mica_core.py so both tools
always agree on package state.

v0.2.6: PCT-010 escalates from WARN to FAIL when mica.yaml sets
di_policy.critical_binding_required: true.
v0.2.7: di_policy.namespace_mode added; no PCT behavior change.

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

from mica_core import MICA_TOOL_VERSION, find_flow_artifact, format_tool_banner, is_closed_contract, run_invocation_trace_checks, run_pct_checks

__version__ = MICA_TOOL_VERSION


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
    print(format_tool_banner("MICA PCT Validator"))
    print(f"Project root: {root}")
    results = run_pct_checks(root)
    closed = _report(results)
    invocation_trace = find_flow_artifact(root, "mica.invocation.jsonl")
    if invocation_trace:
        print("Invocation trace summary:")
        print()
        for cid, status, msg in run_invocation_trace_checks(root):
            print(f"{cid} [{status:<4}] {msg}")
        print()
    sys.exit(0 if closed else 1)


if __name__ == "__main__":
    main()

