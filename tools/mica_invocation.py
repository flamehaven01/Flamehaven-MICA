#!/usr/bin/env python3
"""
MICA Invocation Trace Validator v0.2.9 -- standalone provenance artifact checker.

Usage:
    python mica_invocation.py [trace_file_or_project_root]

Exit code: 0 = invocation trace valid, 1 = missing or invalid trace
"""

from __future__ import annotations

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from mica_core import (
    MICA_TOOL_VERSION,
    find_invocation_schema,
    format_tool_banner,
    run_invocation_trace_checks,
)

__version__ = MICA_TOOL_VERSION


def _report(results: list[tuple[str, str, str]]) -> bool:
    print()
    failed = False
    warned = False
    for cid, status, message in results:
        print(f"{cid} [{status:<4}] {message}")
        if status == "FAIL":
            failed = True
        elif status == "WARN":
            warned = True
    print()
    if failed:
        verdict = "INVALID INVOCATION TRACE"
    elif warned:
        # A stale capsule is a truthful record of a past invocation, not an
        # invalid one. It is reported, and it does not fail the run.
        verdict = "VALID INVOCATION TRACE (stale evidence)"
    else:
        verdict = "VALID INVOCATION TRACE"
    print("Overall:", verdict)
    print()
    return not failed


def main() -> None:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    print(format_tool_banner("MICA Invocation Trace Validator"))
    print(f"Target: {target}")
    print(f"Schema: {find_invocation_schema()}")
    results = run_invocation_trace_checks(target)
    valid = _report(results)
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
