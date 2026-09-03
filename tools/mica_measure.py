#!/usr/bin/env python3
"""
MICA measurement -- what a session is actually given, in numbers.

MICA has had no metrics. Every claim about it has been structural ("the check
fires") rather than quantitative ("the session receives N bytes"). This reports
what is deterministically observable about a package at session start.

What it measures:
  - context budget: bytes delivered to agent context, per profile
  - surface resolution: declared / invoked / agent_context / operator_only
  - capsule coverage: whether the exact invoked bytes can be identified
  - verdict axes and mica_spec lag

What it does NOT measure: whether any of this improves task outcomes. That
needs sessions with a control, not a static scan. Do not read these numbers as
evidence that MICA works.

Usage:
    python mica_measure.py <project_root> [<project_root> ...] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from mica_core import (  # noqa: E402
    MICA_TOOL_VERSION,
    evaluate_axes,
    find_mica_yaml,
    format_tool_banner,
    load_yaml,
    run_pct_checks,
)
from mica_runtime import build_summary  # noqa: E402

__version__ = MICA_TOOL_VERSION


def _spec_note(results: list[tuple[str, str, str]]) -> str | None:
    """Whatever PCT-006 said about the declared spec, rather than a second opinion.

    An earlier draft of this tool recomputed the version gap itself. Two
    implementations of the same comparison is exactly the drift MICA exists to
    catch, so it reads the check's own output instead.
    """
    for pid, status, message in results:
        if pid == "PCT-006" and status == "WARN" and "canonical" in message:
            return message
    return None


def _context_bytes(summary: dict[str, Any]) -> tuple[int, int, int]:
    """Bytes delivered to agent context, to operator only, and in total.

    Read from surface_evidence, so a sectioned delivery counts the slice that
    was actually delivered rather than the file it came from.
    """
    agent = operator = 0
    for entry in summary.get("surface_evidence") or []:
        size = entry.get("bytes") or 0
        if entry.get("audience") == "agent_context":
            agent += size
        else:
            operator += size
    return agent, operator, agent + operator


def measure(project_root: Path, profile: str | None = None) -> dict[str, Any]:
    summary = build_summary(project_root, profile)
    results = run_pct_checks(project_root, profile)
    axes = evaluate_axes(results)

    yaml_path = find_mica_yaml(project_root)
    declared_spec = str((load_yaml(yaml_path) or {}).get("mica_spec", "")) if yaml_path else ""
    spec_note = _spec_note(results)

    agent_bytes, operator_bytes, total_bytes = _context_bytes(summary)
    evidence = summary.get("surface_evidence") or []

    return {
        "package": summary.get("name") or project_root.name,
        "project_root": str(project_root),
        "mica_spec": declared_spec or None,
        "spec_note": spec_note,
        "mode": summary.get("mode"),
        "profile": summary.get("active_profile"),
        "declared_profiles": summary.get("declared_profiles") or [],
        "axes": axes,
        "surfaces": {
            "declared": len(summary.get("declared_surfaces") or []),
            "invoked": len(summary.get("loaded_surfaces") or []),
            "agent_context": len(summary.get("agent_context_surfaces") or []),
            "operator_only": len(summary.get("operator_only_surfaces") or []),
            "deferred": len(summary.get("deferred_surfaces") or []),
            "missing": len(summary.get("missing_invoked_surfaces") or []),
        },
        "context_budget": {
            "agent_context_bytes": agent_bytes,
            "operator_only_bytes": operator_bytes,
            "total_resolved_bytes": total_bytes,
            "sectioned_surfaces": sum(1 for e in evidence if e.get("sections")),
        },
        # A v1 trace records surface roles. A v2 capsule records the digest of
        # each delivered surface, which is what makes "these exact bytes" a
        # checkable claim rather than an assertion.
        "capsule_coverage": {
            "surfaces_with_digest": len(evidence),
            "identifies_exact_bytes": bool(evidence),
            "trace_state": summary.get("invocation_evidence"),
        },
    }


def _print_report(rows: list[dict[str, Any]]) -> None:
    print(
        f"{'PACKAGE':24}{'SPEC':>8}{'CONTRACT':>11}{'CTX BYTES':>12}"
        f"{'CTX/DECL':>10}{'PROFILES':>10}"
    )
    for row in rows:
        s = row["surfaces"]
        ratio = f"{s['agent_context']}/{s['declared']}"
        profiles = str(len(row["declared_profiles"]) or "-")
        print(
            f"{row['package'][:23]:24}"
            f"{str(row['mica_spec'] or '-'):>8}"
            f"{row['axes']['contract']:>11}"
            f"{row['context_budget']['agent_context_bytes']:>12,}"
            f"{ratio:>10}"
            f"{profiles:>10}"
        )

    notes = [(r["package"], r["spec_note"]) for r in rows if r["spec_note"]]
    if notes:
        print()
        for pkg, note in notes:
            print(f"  {pkg[:23]:24} {note}")

    print()
    total_ctx = sum(r["context_budget"]["agent_context_bytes"] for r in rows)
    with_profiles = sum(1 for r in rows if r["declared_profiles"])
    with_digest = sum(1 for r in rows if r["capsule_coverage"]["identifies_exact_bytes"])
    closed = sum(1 for r in rows if r["axes"]["contract"] == "CLOSED")
    print(f"packages                    : {len(rows)}")
    print(f"contract closed             : {closed}/{len(rows)}")
    print(f"declare memory profiles     : {with_profiles}/{len(rows)}")
    print(f"can identify invoked bytes  : {with_digest}/{len(rows)}")
    print(f"agent context bytes (total) : {total_ctx:,}")
    print()
    print("Measures what is structurally observable. Says nothing about whether")
    print("any of it improves task outcomes -- that needs sessions with a control.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure MICA packages")
    parser.add_argument("roots", nargs="+", help="project roots to measure")
    parser.add_argument("--profile", help="memory profile to resolve under")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    rows = []
    for raw in args.roots:
        root = Path(raw).resolve()
        if not root.is_dir():
            print(f"[SKIP] not a directory: {root}", file=sys.stderr)
            continue
        try:
            rows.append(measure(root, args.profile))
        except Exception as exc:  # a broken package must not hide the rest
            print(f"[SKIP] {root.name}: {type(exc).__name__}: {exc}", file=sys.stderr)

    if args.json:
        print(json.dumps(rows, indent=2))
        return

    print(format_tool_banner("MICA Measurement"))
    print()
    _print_report(rows)


if __name__ == "__main__":
    main()
