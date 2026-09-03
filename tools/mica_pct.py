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

v3.0.0 P0: results report on three separate axes. The invocation contract
covers only whether declared memory reached the session. Archive content
quality and memory-authoring integrity report alongside it and no longer
break the contract.

Usage:
    python mica_pct.py [project_root] [--strict]

Exit code: 0 = invocation contract closed, 1 = contract incomplete.
With --strict, an archive or flow FAILURE also exits 1.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from mica_core import (
    MICA_TOOL_VERSION,
    evaluate_axes,
    failing_axes,
    find_flow_artifact,
    format_tool_banner,
    run_invocation_trace_checks,
    run_pct_checks,
)

__version__ = MICA_TOOL_VERSION


def _report(results: list[tuple[str, str, str]]) -> dict[str, str]:
    print()
    for pid, status, msg in results:
        print(f"{pid} [{status:<4}] {msg}")
    print()
    axes = evaluate_axes(results)
    print(f"Contract : {axes['contract']}")
    print(f"Archive  : {axes['archive']}")
    print(f"Flow     : {axes['flow']}")
    print()
    print(
        "Overall:",
        "CLOSED CONTRACT" if axes["contract"] == "CLOSED" else "INCOMPLETE",
    )
    print()
    return axes


def main() -> None:
    # Hand-rolled argument stripping silently accepted --profile and then
    # validated the default profile instead. argparse rejects what it does not
    # know rather than ignoring it.
    parser = argparse.ArgumentParser(description="Validate a MICA package contract")
    parser.add_argument("project_root", nargs="?", default=".", help="package root to validate")
    parser.add_argument(
        "--profile",
        help="memory profile declared under invocation_protocol.profiles",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on an archive or flow failure, not just a contract failure",
    )
    args = parser.parse_args()

    strict = args.strict
    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"[ERROR] Not a directory: {root}")
        sys.exit(1)
    print(format_tool_banner("MICA PCT Validator"))
    print(f"Project root: {root}")
    if args.profile:
        print(f"Profile     : {args.profile}")
    results = run_pct_checks(root, args.profile)
    _report(results)
    trace_failed = False
    invocation_trace = find_flow_artifact(root, "mica.invocation.jsonl")
    if invocation_trace:
        print("Invocation trace summary:")
        print()
        for cid, status, msg in run_invocation_trace_checks(root):
            print(f"{cid} [{status:<4}] {msg}")
            if status == "FAIL":
                trace_failed = True
        print()
        if trace_failed:
            print("[TRACE] recorded invocation evidence is invalid; see IVC-* above")
            print()
    failing = failing_axes(results)
    if not strict:
        failing = [axis for axis in failing if axis == "contract"]
    # A recorded trace that fails IVC-* is invalid evidence about this package.
    # Reporting it while exiting 0 let a corrupted capsule pass a CI gate.
    if trace_failed:
        failing = failing + ["invocation_trace"]
    if failing:
        print(f"[EXIT 1] failing: {failing}")
    sys.exit(1 if failing else 0)


if __name__ == "__main__":
    main()
