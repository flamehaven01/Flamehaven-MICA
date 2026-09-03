#!/usr/bin/env python3
"""
MICA invocation evidence -- proving what actually reached the session.

Invocation has two halves. mica_core resolves which memory a session should
receive; this module validates the record of what it did receive: the capsule's
shape, its internal coherence, and whether the recorded digests still describe
the bytes on disk.

Delivery states stop short of any claim about comprehension. "emitted" means an
adapter reported bytes written to its channel. Nothing here means read,
understood, or obeyed.

Extracted from mica_core.py at v3.0.0 Origin P3b. These checks were one
critical and four high findings inside a 1,893-line module.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from mica_primitives import (
    _is_non_empty_string,
    _resolve_within_root,
    find_flow_artifact,
    find_invocation_schema,
    hash_bytes,
    hash_surface_bytes,
    load_jsonl,
    select_markdown_sections,
)

_SURFACE_EVIDENCE_FIELDS = ("role", "path", "sha256", "bytes", "audience", "delivery_state")

_SURFACE_EVIDENCE_OPTIONAL_FIELDS = ("sections",)

# project_root is an absolute, machine-specific path and is excluded so that the
# same invocation hashes identically on every platform.

_CAPSULE_HASH_FIELDS = (
    "schema_version",
    "invocation_id",
    "timestamp_utc",
    "session_id",
    "trigger",
    "profile",
    "surface_evidence",
    "package_state",
    "core_state",
    "flow_state",
    "mode",
    "pattern",
    "invocation_contract",
    "loaded_surfaces",
    "agent_context_surfaces",
    "operator_only_surfaces",
    "deferred_surfaces",
    "missing_invoked_surfaces",
    "active_critical_invariants",
)

_INVOCATION_REQUIRED_FIELDS = (
    "schema_version",
    "invocation_id",
    "timestamp_utc",
    "project_root",
    "project",
    "package_state",
    "core_state",
    "flow_state",
    "mode",
    "pattern",
    "session_id",
    "invocation_contract",
    "loaded_surfaces",
    "agent_context_surfaces",
    "deferred_surfaces",
    "missing_invoked_surfaces",
    "active_critical_invariants",
    "last_updated",
)

INVOCATION_SCHEMA_V1 = "mica.invocation.v1"

INVOCATION_SCHEMA_V2 = "mica.invocation.v2"

_SUPPORTED_INVOCATION_SCHEMAS = frozenset({INVOCATION_SCHEMA_V1, INVOCATION_SCHEMA_V2})

# Delivery states are monotonic within one invocation and deliberately stop short
# of any claim about comprehension. "emitted" means a MICA adapter reported that
# bytes were written to its output channel; it never means read, understood, or
# obeyed. "acknowledged" requires an independently supplied host reference and is
# not produced by this tool.

DELIVERY_STATES = ("declared", "resolved", "emitted", "acknowledged")

# Audience values reuse the existing invocation-protocol surface separation.

SURFACE_AUDIENCES = ("agent_context", "operator_only", "deferred")


def _is_unique_string_list(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    normalized = [item for item in value if _is_non_empty_string(item)]
    return len(normalized) == len(value) == len(set(normalized))


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_capsule_hash(record: dict[str, Any]) -> str:
    """Deterministic hash over the continuity-relevant fields of one record.

    Field set, ordering, separators, and encoding are pinned so that two
    implementations produce the same hash for the same capsule. The hash never
    covers itself or the absolute project_root.
    """
    payload = {field: record.get(field) for field in _CAPSULE_HASH_FIELDS if field in record}
    return f"sha256:{hashlib.sha256(_canonical_json(payload).encode('utf-8')).hexdigest()}"


def _check_capsule_schema(index: int, record: dict[str, Any]) -> list[str]:
    """Structural checks for the v2 continuity fields."""
    issues: list[str] = []

    trigger = record.get("trigger")
    if trigger is not None:
        if not isinstance(trigger, dict):
            issues.append(f"record {index}: trigger must be an object or null")
        else:
            if not _is_non_empty_string(trigger.get("kind")):
                issues.append(f"record {index}: trigger.kind must be a non-empty string")
            if trigger.get("ref") is not None and not _is_non_empty_string(trigger.get("ref")):
                issues.append(f"record {index}: trigger.ref must be a non-empty string or null")

    evidence = record.get("surface_evidence")
    if not isinstance(evidence, list):
        issues.append(f"record {index}: surface_evidence must be a list")
        return issues

    seen_roles: set[str] = set()
    seen_paths: set[str] = set()
    for position, entry in enumerate(evidence, start=1):
        label = f"record {index} surface_evidence[{position}]"
        if not isinstance(entry, dict):
            issues.append(f"{label}: must be an object")
            continue
        missing = [field for field in _SURFACE_EVIDENCE_FIELDS if field not in entry]
        if missing:
            issues.append(f"{label}: missing fields {missing}")
            continue

        role = entry.get("role")
        if not _is_non_empty_string(role):
            issues.append(f"{label}: invalid role")
        elif role in seen_roles:
            issues.append(f"{label}: duplicate role {role!r}")
        else:
            seen_roles.add(str(role))

        path = entry.get("path")
        if not _is_non_empty_string(path):
            issues.append(f"{label}: invalid path")
        else:
            path_text = str(path)
            if "\\" in path_text:
                issues.append(f"{label}: path must use forward slashes, got {path_text!r}")
            elif path_text.startswith("/") or re.match(r"^[A-Za-z]:", path_text):
                issues.append(f"{label}: path must be repository-relative, got {path_text!r}")
            elif ".." in Path(path_text).parts:
                issues.append(f"{label}: path must not escape the project root")
            elif path_text in seen_paths:
                issues.append(f"{label}: duplicate path {path_text!r}")
            else:
                seen_paths.add(path_text)

        digest = entry.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            issues.append(f"{label}: sha256 must match 'sha256:<64 hex>'")

        size = entry.get("bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            issues.append(f"{label}: bytes must be a non-negative integer")

        if entry.get("audience") not in SURFACE_AUDIENCES:
            issues.append(f"{label}: invalid audience {entry.get('audience')!r}")

        if entry.get("delivery_state") not in DELIVERY_STATES:
            issues.append(f"{label}: invalid delivery_state {entry.get('delivery_state')!r}")

        unknown = [
            key
            for key in entry
            if key not in _SURFACE_EVIDENCE_FIELDS and key not in _SURFACE_EVIDENCE_OPTIONAL_FIELDS
        ]
        if unknown:
            issues.append(f"{label}: unexpected fields {sorted(unknown)}")

        sections = entry.get("sections")
        if sections is not None and not _is_unique_string_list(sections):
            issues.append(f"{label}: sections must be a unique non-empty string list")

    capsule_hash = record.get("capsule_hash")
    if not isinstance(capsule_hash, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", capsule_hash):
        issues.append(f"record {index}: capsule_hash must match 'sha256:<64 hex>'")

    return issues


def _check_capsule_coherence(
    index: int,
    record: dict[str, Any],
    loaded_surfaces: list[Any],
    operator_surfaces: list[Any],
) -> list[str]:
    """Cross-field truthfulness checks for the v2 continuity fields."""
    issues: list[str] = []
    evidence = record.get("surface_evidence")
    if not isinstance(evidence, list):
        return issues

    entries = [entry for entry in evidence if isinstance(entry, dict)]
    context_surfaces = (
        record.get("agent_context_surfaces")
        if isinstance(record.get("agent_context_surfaces"), list)
        else []
    )

    # Evidence must account for every loaded surface. A subset would let a
    # record claim a loaded surface while silently omitting its bytes.
    evidence_roles = {entry.get("role") for entry in entries}
    unaccounted = [role for role in loaded_surfaces if role not in evidence_roles]
    if unaccounted:
        issues.append(f"record {index}: loaded surfaces without surface_evidence {unaccounted}")

    for entry in entries:
        role = entry.get("role")
        audience = entry.get("audience")
        if role not in loaded_surfaces:
            issues.append(
                f"record {index}: surface_evidence role {role!r} is not in loaded_surfaces"
            )
        if audience == "agent_context":
            if role in operator_surfaces:
                issues.append(
                    f"record {index}: operator_only surface {role!r} recorded as agent_context evidence"
                )
            elif role not in context_surfaces:
                issues.append(
                    f"record {index}: {role!r} labeled agent_context but absent from agent_context_surfaces"
                )
        elif audience == "operator_only" and role in context_surfaces:
            issues.append(
                f"record {index}: {role!r} labeled operator_only but present in agent_context_surfaces"
            )

    # A null session cannot carry evidence attributed to an identified AI session.
    if record.get("session_id") is None:
        overclaimed = [
            entry.get("role")
            for entry in entries
            if entry.get("delivery_state") in {"emitted", "acknowledged"}
        ]
        if overclaimed:
            issues.append(
                f"record {index}: null session_id cannot claim delivery for {overclaimed}"
            )

    expected_hash = compute_capsule_hash(record)
    if record.get("capsule_hash") != expected_hash:
        issues.append(
            f"record {index}: capsule_hash mismatch (recorded {record.get('capsule_hash')!r}, "
            f"recomputed {expected_hash!r})"
        )

    return issues


def run_invocation_trace_checks(target: Path) -> list[tuple[str, str, str]]:
    trace_path = target
    project_root: Path | None = None
    schema_path = find_invocation_schema()
    schema_result = (
        "IVC-000",
        "PASS" if schema_path.exists() else "FAIL",
        f"invocation schema {'present' if schema_path.exists() else 'missing'} ({schema_path})",
    )
    if target.is_dir():
        project_root = target
        resolved = find_flow_artifact(target, "mica.invocation.jsonl")
        if not resolved:
            return [schema_result, ("IVC-001", "FAIL", "mica.invocation.jsonl missing")]
        trace_path = resolved
    if not trace_path.exists():
        return [schema_result, ("IVC-001", "FAIL", f"invocation trace missing: {trace_path}")]

    results: list[tuple[str, str, str]] = [
        schema_result,
        ("IVC-001", "PASS", f"invocation trace present ({trace_path})"),
    ]
    try:
        records = load_jsonl(trace_path)
    except Exception as exc:
        return results + [("IVC-002", "FAIL", f"cannot parse invocation trace: {exc}")]
    if not records:
        return results + [("IVC-002", "FAIL", "invocation trace empty")]
    results.append(("IVC-002", "PASS", f"parseable invocation trace ({len(records)} records)"))

    schema_issues: list[str] = []
    coherence_issues: list[str] = []
    allowed_package_states = {"INVOCATION_MODE", "LEGACY_MODE", "INACTIVE"}
    allowed_core_states = {"CLOSED", "INCOMPLETE", "LEGACY", "INACTIVE"}
    allowed_flow_states = {None, "FLOW_OFFLINE", "FLOW_ENABLED", "FLOW_DEGRADED"}
    allowed_modes = {None, "memory_injection", "protocol_evolution", "memory_first"}
    allowed_patterns = {
        None,
        "readme_protocol",
        "hook_trigger",
        "agent_yaml_bootstrap",
        "global_skill",
        "workspace_directive",
        "explicit",
        "legacy",
    }
    allowed_contracts = {None, "memory_first", "archive_first", "legacy_archive"}

    for index, record in enumerate(records, start=1):
        missing = [field for field in _INVOCATION_REQUIRED_FIELDS if field not in record]
        if missing:
            schema_issues.append(f"record {index}: missing required fields {missing}")
            continue
        if record.get("schema_version") not in _SUPPORTED_INVOCATION_SCHEMAS:
            schema_issues.append(
                f"record {index}: unsupported schema_version {record.get('schema_version')}"
            )
        if not _is_non_empty_string(record.get("invocation_id")):
            schema_issues.append(f"record {index}: invalid invocation_id")
        if not _is_non_empty_string(record.get("timestamp_utc")):
            schema_issues.append(f"record {index}: invalid timestamp_utc")
        if not _is_non_empty_string(record.get("project_root")):
            schema_issues.append(f"record {index}: invalid project_root")
        project = record.get("project")
        if not isinstance(project, dict) or "name" not in project or "version" not in project:
            schema_issues.append(f"record {index}: project must expose name and version")
        if record.get("package_state") not in allowed_package_states:
            schema_issues.append(
                f"record {index}: invalid package_state {record.get('package_state')!r}"
            )
        if record.get("core_state") not in allowed_core_states:
            schema_issues.append(f"record {index}: invalid core_state {record.get('core_state')!r}")
        if record.get("flow_state") not in allowed_flow_states:
            schema_issues.append(f"record {index}: invalid flow_state {record.get('flow_state')!r}")
        if record.get("mode") not in allowed_modes:
            schema_issues.append(f"record {index}: invalid mode {record.get('mode')!r}")
        if record.get("pattern") not in allowed_patterns:
            schema_issues.append(f"record {index}: invalid pattern {record.get('pattern')!r}")
        if record.get("invocation_contract") not in allowed_contracts:
            schema_issues.append(
                f"record {index}: invalid invocation_contract {record.get('invocation_contract')!r}"
            )
        if record.get("session_id") is not None and not _is_non_empty_string(
            record.get("session_id")
        ):
            schema_issues.append(f"record {index}: invalid session_id")

        for field in (
            "loaded_surfaces",
            "agent_context_surfaces",
            "operator_only_surfaces",
            "deferred_surfaces",
            "missing_invoked_surfaces",
            "active_critical_invariants",
        ):
            value = (
                record.get(field, []) if field == "operator_only_surfaces" else record.get(field)
            )
            if not _is_unique_string_list(value):
                schema_issues.append(f"record {index}: {field} must be a unique string list")

        loaded_surfaces = (
            record.get("loaded_surfaces") if isinstance(record.get("loaded_surfaces"), list) else []
        )
        context_surfaces = (
            record.get("agent_context_surfaces")
            if isinstance(record.get("agent_context_surfaces"), list)
            else []
        )
        operator_surfaces = (
            record.get("operator_only_surfaces")
            if isinstance(record.get("operator_only_surfaces"), list)
            else []
        )
        deferred_surfaces = (
            record.get("deferred_surfaces")
            if isinstance(record.get("deferred_surfaces"), list)
            else []
        )
        missing_invoked_surfaces = (
            record.get("missing_invoked_surfaces")
            if isinstance(record.get("missing_invoked_surfaces"), list)
            else []
        )

        extra_context = [surface for surface in context_surfaces if surface not in loaded_surfaces]
        if extra_context:
            coherence_issues.append(
                f"record {index}: agent_context_surfaces not loaded {extra_context}"
            )
        overlapping_operator = [
            surface for surface in operator_surfaces if surface in context_surfaces
        ]
        if overlapping_operator:
            coherence_issues.append(
                f"record {index}: operator_only_surfaces overlap agent_context_surfaces {overlapping_operator}"
            )
        overlapping_deferred = [
            surface for surface in deferred_surfaces if surface in loaded_surfaces
        ]
        if overlapping_deferred:
            coherence_issues.append(
                f"record {index}: deferred_surfaces overlap loaded_surfaces {overlapping_deferred}"
            )
        if record.get("schema_version") == INVOCATION_SCHEMA_V2:
            schema_issues.extend(_check_capsule_schema(index, record))
            coherence_issues.extend(
                _check_capsule_coherence(index, record, loaded_surfaces, operator_surfaces)
            )

        overlapping_missing = [
            surface for surface in missing_invoked_surfaces if surface in loaded_surfaces
        ]
        if overlapping_missing:
            coherence_issues.append(
                f"record {index}: missing_invoked_surfaces overlap loaded_surfaces {overlapping_missing}"
            )

    if schema_issues:
        preview = "; ".join(schema_issues[:4])
        if len(schema_issues) > 4:
            preview += f"; ... (+{len(schema_issues) - 4} more)"
        results.append(("IVC-003", "FAIL", preview))
    else:
        results.append(
            (
                "IVC-003",
                "PASS",
                "invocation trace shape matches supported schema expectations "
                f"({', '.join(sorted(_SUPPORTED_INVOCATION_SCHEMAS))})",
            )
        )

    if coherence_issues:
        preview = "; ".join(coherence_issues[:4])
        if len(coherence_issues) > 4:
            preview += f"; ... (+{len(coherence_issues) - 4} more)"
        results.append(("IVC-004", "FAIL", preview))
    else:
        results.append(("IVC-004", "PASS", "invocation surfaces are internally coherent"))

    record_is_sound = not any(
        cid in {"IVC-003", "IVC-004"} and status == "FAIL" for cid, status, _ in results
    )
    results.append(_check_live_surface_bytes(project_root, records, record_is_sound))

    return results


def _check_live_surface_bytes(
    project_root: Path | None,
    records: list[dict[str, Any]],
    record_is_sound: bool,
) -> tuple[str, str, str]:
    """IVC-005: compare the newest capsule's digests against the bytes on disk.

    Drift is reported as WARN, not FAIL. An older record was true when written,
    so a changed surface makes the capsule stale rather than invalid. The
    operator re-invokes to record current bytes.

    Nothing is read from disk unless the record already passed the schema and
    coherence checks. An unsound record must not be able to direct the
    validator at a file, and a recorded path is re-resolved against the root
    before it is opened.
    """
    if project_root is None:
        return (
            "IVC-005",
            "INFO",
            "project root not supplied; recorded digests not compared against disk",
        )
    if not record_is_sound:
        return (
            "IVC-005",
            "INFO",
            "skipped: trace failed schema or coherence checks; no disk access performed",
        )

    newest = None
    for record in reversed(records):
        if not isinstance(record, dict):
            continue
        if record.get("schema_version") != INVOCATION_SCHEMA_V2:
            continue
        evidence = record.get("surface_evidence")
        if isinstance(evidence, list) and evidence:
            newest = record
            break

    if newest is None:
        return ("IVC-005", "INFO", "no v2 capsule with surface evidence; nothing to re-hash")

    drifted: list[str] = []
    for entry in newest.get("surface_evidence") or []:
        if not isinstance(entry, dict):
            continue
        role = str(entry.get("role"))
        current = rehash_evidence_entry(project_root, entry)
        if isinstance(current, str):
            drifted.append(f"{role} ({current})")
            continue
        digest, size = current
        if digest != entry.get("sha256") or size != entry.get("bytes"):
            drifted.append(f"{role} (bytes changed)")

    if drifted:
        return (
            "IVC-005",
            "WARN",
            f"recorded capsule {newest.get('invocation_id')} no longer matches disk: "
            f"{drifted} -- re-invoke to record current bytes",
        )
    return (
        "IVC-005",
        "PASS",
        f"capsule {newest.get('invocation_id')} digests match the current surface bytes",
    )


def rehash_evidence_entry(project_root: Path, entry: dict[str, Any]) -> tuple[str, int] | str:
    """Recompute the digest a recorded evidence entry should have right now.

    Returns (sha256, bytes) or a string describing why it cannot be compared.
    Both the write-time re-resolve and IVC-005 go through here so a sectioned
    capsule is never compared against the whole file it was sliced from.
    """
    rel = entry.get("path")
    if not _is_non_empty_string(rel):
        return "unusable path"
    path = _resolve_within_root(project_root, str(rel))
    if path is None:
        return "path escapes project root; not read"
    if not path.is_file():
        return "missing"

    wanted = entry.get("sections")
    try:
        if isinstance(wanted, list) and wanted:
            delivered, absent = select_markdown_sections(
                path.read_text(encoding="utf-8"), [str(name) for name in wanted]
            )
            if absent:
                return f"sections removed: {absent}"
            return hash_bytes(delivered.encode("utf-8"))
        return hash_surface_bytes(path)
    except (OSError, UnicodeDecodeError):
        return "unreadable"
