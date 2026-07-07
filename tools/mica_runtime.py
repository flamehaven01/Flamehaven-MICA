#!/usr/bin/env python3
"""
MICA runtime summary utility v0.2.8.

Usage:
    python tools/mica_runtime.py [project_root] --format text
    python tools/mica_runtime.py [project_root] --format hook
    python tools/mica_runtime.py [project_root] --format json

v0.2.5: pct_status() delegates to mica_core.run_pct_checks() so both tools agree.
v0.2.6: PCT-010 escalates from WARN to FAIL when mica.yaml sets
        di_policy.critical_binding_required: true. No runtime.py changes required.
v0.2.7: COMPACT_MODE formally defined; di_policy.namespace_mode added. No runtime
        behavior changes required -- COMPACT_MODE uses existing LEGACY_MODE path.

Unreleased working-tree draft: text/json output can surface separate Core and Flow
states for v0.2.9 flow-enabled packages without changing legacy hook output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from mica_core import (
    MICA_TOOL_VERSION,
    find_flow_artifact,
    find_legacy_archive,
    find_mica_yaml,
    is_closed_contract,
    load_json,
    load_yaml,
    run_pct_checks,
)

__version__ = MICA_TOOL_VERSION


def detect_state(project_root: Path) -> tuple[str, Path | None, Path | None]:
    mica_yaml = find_mica_yaml(project_root)
    if mica_yaml:
        return ("INVOCATION_MODE", mica_yaml, None)
    archive = find_legacy_archive(project_root)
    if archive:
        return ("LEGACY_MODE", None, archive)
    return ("INACTIVE", None, None)


def resolve_paths(
    project_root: Path, mica_yaml_path: Path
) -> tuple[dict[str, Any], Path | None, Path | None]:
    yd = load_yaml(mica_yaml_path)
    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
    archive_path: Path | None = None
    playbook_path: Path | None = None
    for lyr in layers:
        if not isinstance(lyr, dict):
            continue
        rel = lyr.get("path")
        if not isinstance(rel, str):
            continue
        role = lyr.get("kind") or lyr.get("name")
        if role == "archive":
            archive_path = project_root / rel
        elif role == "playbook":
            playbook_path = project_root / rel
    return yd, archive_path, playbook_path


def count_invariants(
    archive: dict[str, Any],
) -> tuple[int, int, list[dict[str, Any]]]:
    dis = archive.get("design_invariants", [])
    if not isinstance(dis, list):
        return (0, 0, [])
    normalized = [d for d in dis if isinstance(d, dict)]
    crit = sum(1 for d in normalized if d.get("severity") == "critical")
    high = sum(1 for d in normalized if d.get("severity") == "high")
    return crit, high, normalized


def _extract_critical_invariants(dis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for d in dis:
        if d.get("severity") != "critical":
            continue
        entry: dict[str, Any] = {"id": d.get("id"), "label": d.get("label")}
        binding = d.get("binding")
        if isinstance(binding, dict):
            entry["binding"] = binding
        result.append(entry)
    return result




def _pct_entry(results: list[tuple[str, str, str]], pct_id: str) -> tuple[str | None, str | None]:
    for pid, status, message in results:
        if pid == pct_id:
            return status, message
    return None, None


def _candidate_counts(project_root: Path) -> tuple[int, int, int]:
    candidates_path = find_flow_artifact(project_root, "mica.candidates.json")
    if not candidates_path:
        return (0, 0, 0)
    doc = load_json(candidates_path)
    candidates = doc.get("candidates") if isinstance(doc.get("candidates"), list) else []
    pending = 0
    approved = 0
    promoted = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        status = candidate.get("status")
        if status == "pending_operator_review":
            pending += 1
        elif status == "approved":
            approved += 1
        elif status == "promoted":
            promoted += 1
    return pending, approved, promoted


def _build_flow_summary(
    project_root: Path, yd: dict[str, Any], pct_results: list[tuple[str, str, str]]
) -> dict[str, Any]:
    flow_policy = yd.get("flow_policy", {}) if isinstance(yd.get("flow_policy"), dict) else {}
    flow_declared = isinstance(yd.get("flow_policy"), dict)
    enabled = bool(flow_policy.get("enabled", False))
    required = bool(flow_policy.get("required", False))

    if not flow_declared and not enabled:
        return {
            "flow_policy_declared": False,
            "flow_enabled": False,
            "flow_required": False,
            "flow_state": None,
            "flow_observation_status": None,
            "flow_promotion_gate": None,
            "flow_candidate_counts": {"pending": 0, "approved": 0, "promoted": 0},
            "flow_reason": None,
        }

    if not enabled:
        return {
            "flow_policy_declared": True,
            "flow_enabled": False,
            "flow_required": required,
            "flow_state": "FLOW_OFFLINE",
            "flow_observation_status": "OFFLINE",
            "flow_promotion_gate": "OFFLINE",
            "flow_candidate_counts": {"pending": 0, "approved": 0, "promoted": 0},
            "flow_reason": None,
        }

    pct013_status, pct013_message = _pct_entry(pct_results, "PCT-013")
    pct014_status, pct014_message = _pct_entry(pct_results, "PCT-014")
    pct015_status, pct015_message = _pct_entry(pct_results, "PCT-015")
    pct017_status, pct017_message = _pct_entry(pct_results, "PCT-017")
    pct018_status, pct018_message = _pct_entry(pct_results, "PCT-018")
    pending, approved, promoted = _candidate_counts(project_root)
    failures = [
        (status, message)
        for status, message in (
            (pct013_status, pct013_message),
            (pct015_status, pct015_message),
            (pct017_status, pct017_message),
        )
        if status == "FAIL"
    ]
    warnings = [
        (status, message)
        for status, message in ((pct014_status, pct014_message), (pct018_status, pct018_message))
        if status == "WARN"
    ]
    flow_state = "FLOW_DEGRADED" if failures or warnings else "FLOW_ENABLED"
    promotion_gate = "FAIL" if pct015_status == "FAIL" or pct017_status == "FAIL" else "PASS"
    if failures:
        flow_reason = failures[0][1]
    elif warnings:
        flow_reason = warnings[0][1]
    else:
        flow_reason = None

    return {
        "flow_policy_declared": True,
        "flow_enabled": True,
        "flow_required": required,
        "flow_state": flow_state,
        "flow_observation_status": pct013_status or "UNKNOWN",
        "flow_promotion_gate": promotion_gate,
        "flow_candidate_counts": {
            "pending": pending,
            "approved": approved,
            "promoted": promoted,
        },
        "flow_reason": flow_reason,
    }

def pct_status(project_root: Path) -> str:
    """
    Returns CLOSED, INCOMPLETE, LEGACY, or INACTIVE.
    Delegates to run_pct_checks() so the verdict matches mica_pct.py exactly.
    """
    mica_yaml = find_mica_yaml(project_root)
    if not mica_yaml:
        return "LEGACY" if find_legacy_archive(project_root) else "INACTIVE"
    results = run_pct_checks(project_root)
    return "CLOSED" if is_closed_contract(results) else "INCOMPLETE"


def build_summary(project_root: Path) -> dict[str, Any]:
    state, mica_yaml, legacy_archive = detect_state(project_root)
    base: dict[str, Any] = {"state": state, "project_root": str(project_root)}

    if state == "INACTIVE":
        base.update(
            {
                "name": None,
                "version": None,
                "mode": None,
                "pattern": None,
                "pct": "INACTIVE",
                "critical_count": 0,
                "high_count": 0,
                "critical_invariants": [],
                "last_updated": None,
                "hook_output": {},
                "core_state": "INACTIVE",
                "flow_state": None,
            }
        )
        return base

    if state == "LEGACY_MODE":
        archive = load_json(legacy_archive)
        crit, high, dis = count_invariants(archive)
        proj = archive.get("project") if isinstance(archive.get("project"), dict) else {}
        base.update(
            {
                "name": proj.get("name"),
                "version": proj.get("version"),
                "mode": None,
                "pattern": "legacy",
                "pct": "LEGACY",
                "critical_count": crit,
                "high_count": high,
                "critical_invariants": _extract_critical_invariants(dis),
                "last_updated": (archive.get("operation_meta") or {}).get("last_updated"),
                "hook_output": {},
                "core_state": "LEGACY",
                "flow_state": None,
            }
        )
        return base

    assert mica_yaml is not None
    yd, archive_path, _playbook_path = resolve_paths(project_root, mica_yaml)
    archive = load_json(archive_path)
    crit, high, dis = count_invariants(archive)
    inv = yd.get("invocation_protocol") if isinstance(yd.get("invocation_protocol"), dict) else {}
    hook_output_raw = inv.get("hook_output") if isinstance(inv.get("hook_output"), dict) else {}
    proj = archive.get("project") if isinstance(archive.get("project"), dict) else {}
    pct_results = run_pct_checks(project_root)
    core_state = "CLOSED" if is_closed_contract(pct_results) else "INCOMPLETE"
    flow_summary = _build_flow_summary(project_root, yd, pct_results)
    base.update(
        {
            "name": yd.get("name") or proj.get("name"),
            "version": proj.get("version"),
            "mode": yd.get("mode"),
            "pattern": inv.get("primary_pattern", "readme_protocol"),
            "pct": core_state,
            "critical_count": crit,
            "high_count": high,
            "critical_invariants": _extract_critical_invariants(dis),
            "last_updated": (archive.get("operation_meta") or {}).get("last_updated"),
            "hook_output": hook_output_raw,
            "core_state": core_state,
        }
    )
    base.update(flow_summary)
    return base


def slug(text: str | None) -> str:
    if not text:
        return ""
    value = re.sub(r"\s+", "-", str(text).strip().lower())
    value = re.sub(r"[^a-z0-9-]", "", value)
    return re.sub(r"-+", "-", value).strip("-")


def emit_text(summary: dict[str, Any]) -> str:
    if summary["state"] == "INACTIVE":
        return "[MICA] INACTIVE -- no mica.yaml or legacy archive found."
    lines = [
        f"[MICA LOADED] {summary.get('name') or 'unknown'} v{summary.get('version') or 'unknown'}",
        f"Mode      : {summary.get('mode') or 'legacy'}",
        f"Pattern   : {summary.get('pattern') or 'legacy'}",
        f"Invariants: {summary.get('critical_count', 0)} critical, {summary.get('high_count', 0)} high",
        f"Last upd  : {summary.get('last_updated') or 'unknown'}",
    ]
    if summary.get("flow_state"):
        counts = summary.get("flow_candidate_counts") if isinstance(summary.get("flow_candidate_counts"), dict) else {}
        lines.extend(
            [
                f"Core      : {summary.get('core_state')}",
                f"Flow      : {summary.get('flow_state')}",
                f"Observation: {summary.get('flow_observation_status')}",
                "Candidates: "
                f"{counts.get('pending', 0)} pending, "
                f"{counts.get('approved', 0)} approved, "
                f"{counts.get('promoted', 0)} promoted",
                f"Promotion gate: {summary.get('flow_promotion_gate')}",
            ]
        )
        if summary.get("flow_reason"):
            lines.append(f"Reason    : {summary.get('flow_reason')}")
    else:
        lines.append(f"PCT       : {summary.get('pct')}")
    crits = summary.get("critical_invariants", []) or []
    if crits:
        lines.append("")
        lines.append("Active critical invariant candidates:")
        for di in crits:
            lines.append(f"  {di.get('id')}: {di.get('label')}")
            binding = di.get("binding")
            if isinstance(binding, dict) and binding.get("origin_episode"):
                vc = binding.get("violation_count")
                vc_str = f" [{vc}x violated]" if isinstance(vc, int) and vc > 0 else ""
                lines.append(f"    Evidence: {binding['origin_episode']}{vc_str}")
    return "\n".join(lines)


def emit_hook(summary: dict[str, Any]) -> str:
    if summary["state"] == "INACTIVE":
        return "[MICA] INACTIVE -- no mica.yaml or legacy archive found."
    first = (
        f"[MICA] {slug(summary.get('name')) or 'unknown'} v{summary.get('version') or 'unknown'}"
        f" | mode={summary.get('mode') or 'legacy'}"
        f" | pattern={summary.get('pattern') or 'legacy'}"
        f" | DI={summary.get('critical_count', 0)}crit/{summary.get('high_count', 0)}high"
        f" | pct={summary.get('pct')}"
        f" | last={summary.get('last_updated') or 'unknown'}"
    )
    hook_output = summary.get("hook_output") if isinstance(summary.get("hook_output"), dict) else {}
    max_di = hook_output.get("max_di_lines")
    di_filter = hook_output.get("di_filter", "all")

    di_lines: list[str] = []
    for di in summary.get("critical_invariants", []) or []:
        if di_filter == "violations_only":
            binding = di.get("binding") if isinstance(di.get("binding"), dict) else {}
            vc = binding.get("violation_count")
            if not (isinstance(vc, int) and vc > 0):
                continue
        if di.get("id") and di.get("label"):
            binding = di.get("binding") if isinstance(di.get("binding"), dict) else {}
            vc = binding.get("violation_count")
            vc_str = f" [{vc}x]" if isinstance(vc, int) and vc > 0 else ""
            di_lines.append(f"[MICA:DI] {di['id']}(critical): {di['label']}{vc_str}")
        if isinstance(max_di, int) and max_di > 0 and len(di_lines) >= max_di:
            break

    return "\n".join([first] + di_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit portable MICA runtime summaries.")
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--format", choices=["text", "json", "hook"], default="text")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists() or not project_root.is_dir():
        print(f"[ERROR] Not a directory: {project_root}", file=sys.stderr)
        sys.exit(1)

    summary = build_summary(project_root)
    if args.format == "json":
        print(json.dumps(summary, indent=2))
    elif args.format == "hook":
        print(emit_hook(summary))
    else:
        print(emit_text(summary))


if __name__ == "__main__":
    main()

