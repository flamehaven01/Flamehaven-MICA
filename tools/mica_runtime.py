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
from datetime import datetime, timezone
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
    layer_role,
    load_json,
    load_jsonl,
    load_yaml,
    resolve_invocation_contract,
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


def resolve_paths(project_root: Path, mica_yaml_path: Path) -> tuple[dict[str, Any], Path | None, Path | None]:
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


def count_invariants(archive: dict[str, Any]) -> tuple[int, int, list[dict[str, Any]]]:
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


def _resolve_declared_layer_paths(project_root: Path, yd: dict[str, Any]) -> dict[str, Path]:
    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
    result: dict[str, Path] = {}
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        role = layer_role(layer)
        rel = layer.get("path")
        if not role or not isinstance(rel, str):
            continue
        result[role] = project_root / rel
    return result


def _default_loaded_surfaces(mode: str | None, declared_roles: list[str]) -> list[str]:
    preferred = ["archive", "playbook", "slots"] if mode == "memory_first" else ["archive", "playbook"]
    return [role for role in preferred if role in declared_roles]


def _default_invocation_trace_path(project_root: Path) -> Path:
    memory_dir = project_root / "memory"
    if memory_dir.exists() and memory_dir.is_dir():
        return memory_dir / "mica.invocation.jsonl"
    return project_root / "mica.invocation.jsonl"


def _resolve_active_session_id(project_root: Path) -> str | None:
    sessions_path = find_flow_artifact(project_root, "mica.sessions.jsonl")
    if sessions_path:
        try:
            session_records = load_jsonl(sessions_path)
        except Exception:
            session_records = []
        for record in reversed(session_records):
            session_id = record.get("session_id") if isinstance(record, dict) else None
            if isinstance(session_id, str) and session_id.strip():
                return session_id

    observe_path = find_flow_artifact(project_root, "mica.observe.jsonl")
    if observe_path:
        try:
            observations = load_jsonl(observe_path)
        except Exception:
            observations = []
        for record in reversed(observations):
            session_id = record.get("session_id") if isinstance(record, dict) else None
            if isinstance(session_id, str) and session_id.strip():
                return session_id

    return None


def _build_invocation_summary(
    project_root: Path,
    state: str,
    mode: str | None,
    yd: dict[str, Any] | None,
    archive_path: Path | None,
    playbook_path: Path | None,
) -> dict[str, Any]:
    if state == "INACTIVE":
        return {
            "session_id": None,
            "invocation_contract": None,
            "declared_surfaces": [],
            "loaded_surfaces": [],
            "agent_context_surfaces": [],
            "deferred_surfaces": [],
            "missing_invoked_surfaces": [],
            "invocation_trace_default_path": str(_default_invocation_trace_path(project_root)),
        }

    if state == "LEGACY_MODE":
        return {
            "session_id": _resolve_active_session_id(project_root),
            "invocation_contract": "legacy_archive",
            "declared_surfaces": ["archive"],
            "loaded_surfaces": ["archive"],
            "agent_context_surfaces": ["archive"],
            "deferred_surfaces": [],
            "missing_invoked_surfaces": [],
            "invocation_trace_default_path": str(_default_invocation_trace_path(project_root)),
        }

    assert yd is not None
    layer_paths = _resolve_declared_layer_paths(project_root, yd)
    if archive_path is not None:
        layer_paths["archive"] = archive_path
    if playbook_path is not None:
        layer_paths["playbook"] = playbook_path

    contract = resolve_invocation_contract(yd)
    declared = list(contract["declared_surfaces"])
    expected_loaded = list(contract["loaded_surfaces"])
    loaded = [role for role in expected_loaded if layer_paths.get(role) and layer_paths[role].exists()]
    deferred = list(contract["deferred_surfaces"])
    missing = [role for role in expected_loaded if role not in loaded]
    agent_context_surfaces = [role for role in contract["agent_context_surfaces"] if role in loaded]
    if not agent_context_surfaces:
        agent_context_surfaces = [role for role in loaded]

    return {
        "session_id": _resolve_active_session_id(project_root),
        "invocation_contract": contract["invocation_contract"],
        "declared_surfaces": declared,
        "loaded_surfaces": loaded,
        "agent_context_surfaces": agent_context_surfaces,
        "deferred_surfaces": deferred,
        "missing_invoked_surfaces": missing,
        "invocation_trace_default_path": str(_default_invocation_trace_path(project_root)),
    }


def _build_flow_summary(project_root: Path, yd: dict[str, Any], pct_results: list[tuple[str, str, str]]) -> dict[str, Any]:
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
            "flow_recall_status": None,
            "flow_telemetry_status": None,
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
            "flow_recall_status": "OFFLINE",
            "flow_telemetry_status": "OFFLINE",
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
        "flow_recall_status": pct014_status or "UNKNOWN",
        "flow_telemetry_status": pct018_status or "UNKNOWN",
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
        base.update(_build_invocation_summary(project_root, state, None, None, None, None))
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
        base.update(_build_invocation_summary(project_root, state, None, None, legacy_archive, None))
        return base

    assert mica_yaml is not None
    yd, archive_path, playbook_path = resolve_paths(project_root, mica_yaml)
    archive = load_json(archive_path)
    crit, high, dis = count_invariants(archive)
    inv = yd.get("invocation_protocol") if isinstance(yd.get("invocation_protocol"), dict) else {}
    hook_output_raw = inv.get("hook_output") if isinstance(inv.get("hook_output"), dict) else {}
    proj = archive.get("project") if isinstance(archive.get("project"), dict) else {}
    pct_results = run_pct_checks(project_root)
    core_state = "CLOSED" if is_closed_contract(pct_results) else "INCOMPLETE"
    flow_summary = _build_flow_summary(project_root, yd, pct_results)
    invocation_summary = _build_invocation_summary(project_root, state, yd.get("mode"), yd, archive_path, playbook_path)
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
    base.update(invocation_summary)
    return base


def build_invocation_trace_record(summary: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    critical_ids = [
        str(item.get("id"))
        for item in summary.get("critical_invariants", []) or []
        if isinstance(item, dict) and item.get("id")
    ]
    return {
        "schema_version": "mica.invocation.v1",
        "invocation_id": f"inv_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "timestamp_utc": now,
        "project_root": summary.get("project_root"),
        "project": {
            "name": summary.get("name"),
            "version": summary.get("version"),
        },
        "package_state": summary.get("state"),
        "core_state": summary.get("core_state"),
        "flow_state": summary.get("flow_state"),
        "mode": summary.get("mode"),
        "pattern": summary.get("pattern"),
        "session_id": summary.get("session_id"),
        "invocation_contract": summary.get("invocation_contract"),
        "loaded_surfaces": list(summary.get("loaded_surfaces") or []),
        "agent_context_surfaces": list(summary.get("agent_context_surfaces") or []),
        "deferred_surfaces": list(summary.get("deferred_surfaces") or []),
        "missing_invoked_surfaces": list(summary.get("missing_invoked_surfaces") or []),
        "active_critical_invariants": critical_ids,
        "last_updated": summary.get("last_updated"),
    }


def write_invocation_trace(project_root: Path, summary: dict[str, Any], output_path: Path | None = None) -> Path:
    path = output_path or Path(str(summary.get("invocation_trace_default_path") or _default_invocation_trace_path(project_root)))
    path.parent.mkdir(parents=True, exist_ok=True)
    record = build_invocation_trace_record(summary)
    serialized = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(serialized)
        fh.write("\n")
    return path


def slug(text: str | None) -> str:
    if not text:
        return ""
    value = re.sub(r"\s+", "-", str(text).strip().lower())
    value = re.sub(r"[^a-z0-9-]", "", value)
    return re.sub(r"-+", "-", value).strip("-")


def _compact_surfaces(values: list[str] | None) -> str:
    items = [str(value) for value in values or [] if str(value).strip()]
    return "+".join(items) if items else "none"


def emit_text(summary: dict[str, Any]) -> str:
    if summary["state"] == "INACTIVE":
        return "[MICA] INACTIVE -- no mica.yaml or legacy archive found."
    loaded_surfaces = ", ".join(summary.get("loaded_surfaces") or []) or "none"
    agent_context_surfaces = ", ".join(summary.get("agent_context_surfaces") or []) or "none"
    deferred_surfaces = ", ".join(summary.get("deferred_surfaces") or []) or "none"
    lines = [
        f"[MICA LOADED] {summary.get('name') or 'unknown'} v{summary.get('version') or 'unknown'}",
        f"Mode      : {summary.get('mode') or 'legacy'}",
        f"Pattern   : {summary.get('pattern') or 'legacy'}",
        f"Invoked   : {loaded_surfaces}",
        f"Context   : {agent_context_surfaces}",
        f"Last upd  : {summary.get('last_updated') or 'unknown'}",
    ]
    if summary.get("deferred_surfaces"):
        lines.append(f"Deferred  : {deferred_surfaces}")
    if summary.get("missing_invoked_surfaces"):
        missing = ", ".join(summary.get("missing_invoked_surfaces") or [])
        lines.append(f"Missing   : {missing}")
    if summary.get("flow_state"):
        counts = summary.get("flow_candidate_counts") if isinstance(summary.get("flow_candidate_counts"), dict) else {}
        lines.extend(
            [
                f"Core      : {summary.get('core_state')}",
                f"Flow      : {summary.get('flow_state')}",
                f"Observation: {summary.get('flow_observation_status')}",
                f"Recall    : {summary.get('flow_recall_status')}",
                f"Telemetry : {summary.get('flow_telemetry_status')}",
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
    lines.append(f"Invariants: {summary.get('critical_count', 0)} critical, {summary.get('high_count', 0)} high")
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
        f" | invoked={_compact_surfaces(summary.get('loaded_surfaces'))}"
        f" | context={_compact_surfaces(summary.get('agent_context_surfaces'))}"
        f" | core={summary.get('core_state') or summary.get('pct')}"
    )
    if summary.get("flow_state"):
        first += (
            f" | flow={summary.get('flow_state')}"
            f" | recall={summary.get('flow_recall_status') or 'UNKNOWN'}"
            f" | telemetry={summary.get('flow_telemetry_status') or 'UNKNOWN'}"
        )
    first += (
        f" | support={summary.get('critical_count', 0)}crit/{summary.get('high_count', 0)}high"
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
    parser.add_argument("--write-invocation-trace", action="store_true")
    parser.add_argument("--trace-file")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists() or not project_root.is_dir():
        print(f"[ERROR] Not a directory: {project_root}", file=sys.stderr)
        sys.exit(1)

    summary = build_summary(project_root)
    trace_path: Path | None = None
    if args.write_invocation_trace or args.trace_file:
        trace_path = write_invocation_trace(
            project_root,
            summary,
            Path(args.trace_file).resolve() if args.trace_file else None,
        )
        summary = dict(summary)
        summary["invocation_trace_path"] = str(trace_path)

    if args.format == "json":
        print(json.dumps(summary, indent=2))
    elif args.format == "hook":
        print(emit_hook(summary))
    else:
        output = emit_text(summary)
        if trace_path is not None:
            output = f"{output}\nInvocation trace: {trace_path}"
        print(output)


if __name__ == "__main__":
    main()
