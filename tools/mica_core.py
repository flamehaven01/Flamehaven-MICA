#!/usr/bin/env python3
"""
MICA core -- shared package resolution and PCT judgment.

Imported by mica_pct.py (full validator) and mica_runtime.py (pct_status query).
Both tools call run_pct_checks() so their PCT verdicts are always aligned.

PyYAML is preferred. When absent, the fallback parser handles MICA's mica.yaml
structure: top-level keys, nested dicts, lists of dicts. Flat-only parsers from
v0.2.4 and earlier could not parse invocation_protocol.hook_output or full
layers[] entries with multiple keys. This parser tracks indentation to handle both.

v0.2.6: PCT-010 escalates from WARN to FAIL when di_policy.critical_binding_required
is set to true in mica.yaml. Opt-in per package; default behavior is unchanged.
v0.2.7: di_policy.namespace_mode added; COMPACT_MODE formally defined.
v0.2.8: PCT-010 quality check (doctrinal vs incident-grounded binding),
        PCT-010 violation_count/last_triggered coherence check,
        PCT-012 archive freshness (opt-in via di_policy.max_archive_age_days),
        PCT-006 canonical version lag warning (>= 2 minor versions behind).

Unreleased working-tree draft: adds flow-plane checks PCT-013, PCT-014, PCT-015, PCT-017, and PCT-018
for v0.2.9 observation, recall coverage, promotion provenance, injection safety, and telemetry completeness.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

# Re-exported so `from mica_core import load_yaml` keeps working in consumer
# packages that vendored an earlier tools/ copy.
from mica_primitives import (  # noqa: E402
    MICA_CANONICAL_VERSION as MICA_CANONICAL_VERSION,
)
from mica_primitives import (
    MICA_TOOL_VERSION as MICA_TOOL_VERSION,
)
from mica_primitives import (
    _coerce as _coerce,
)
from mica_primitives import (
    _is_non_empty_string as _is_non_empty_string,
)
from mica_primitives import (
    _minimal_yaml_parse as _minimal_yaml_parse,
)
from mica_primitives import (
    _normalized_json_text as _normalized_json_text,
)
from mica_primitives import (
    _parse_block as _parse_block,
)
from mica_primitives import (
    _parse_list as _parse_list,
)
from mica_primitives import (
    _resolve_within_root as _resolve_within_root,
)
from mica_primitives import (
    _tokenize as _tokenize,
)
from mica_primitives import (
    canonical_surface_path as canonical_surface_path,
)
from mica_primitives import (
    find_flow_artifact as find_flow_artifact,
)
from mica_primitives import (
    find_invocation_schema as find_invocation_schema,
)
from mica_primitives import (
    format_tool_banner as format_tool_banner,
)
from mica_primitives import (
    hash_bytes as hash_bytes,
)
from mica_primitives import (
    hash_surface_bytes as hash_surface_bytes,
)
from mica_primitives import (
    load_json as load_json,
)
from mica_primitives import (
    load_jsonl as load_jsonl,
)
from mica_primitives import (
    load_yaml as load_yaml,
)
from mica_primitives import (
    parse_markdown_sections as parse_markdown_sections,
)
from mica_primitives import (
    select_markdown_sections as select_markdown_sections,
)

# MICA is a memory and playbook package, not a governance engine. The contract
# it makes is about invocation: did the declared memory surfaces actually reach
# this session, and did anything reach it that should not have?
#
# Archive content quality and memory-authoring integrity matter, but they are
# supporting concerns. They report on their own axes and do not break the
# invocation contract. v3.0.0-declaration said this in prose; these three sets
# are that statement in code.
CONTRACT_CHECKS = frozenset(
    {
        "PCT-001",  # mica.yaml present
        "PCT-002",  # required fields + archive/playbook layers declared
        "PCT-003",  # declared layer paths resolve
        "PCT-004",  # mode and layer roles cohere
        "PCT-007",  # invocation protocol / agent_context surfaces
        "PCT-008",  # hook carrier present when declared
        "PCT-017",  # unapproved memory must not enter agent_context
    }
)

# Is the memory content well formed? Opt-in escalation (di_policy) still
# applies here; it just reports on this axis instead of the contract.
ARCHIVE_CHECKS = frozenset({"PCT-005", "PCT-006", "PCT-010", "PCT-011", "PCT-012"})

# Is the memory-authoring pipeline coherent? Producing memory is a different
# job from invoking it.
FLOW_CHECKS = frozenset({"PCT-013", "PCT-014", "PCT-015", "PCT-018"})

# Retained for consumer packages that vendored an earlier tools/ copy. The set
# is now contract-only; archive and flow failures no longer appear here.
HARD_FAIL_CHECKS = CONTRACT_CHECKS

_EPISODE_PATTERNS = [
    re.compile(r"EXP-[A-Z]"),  # episode code: EXP-OS-1, EXP-PN-2
    re.compile(r"v\d+\.\d+"),  # version ref: v0.8.6, v1.2
    re.compile(r"\d{4}-\d{2}-\d{2}"),  # ISO date: 2026-04-07
    re.compile(r"\d{4}-\d{2}"),  # year-month: 2026-04
    re.compile(r"#\d+"),  # issue number: #123
]


# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------


def find_mica_yaml(project_root: Path) -> Path | None:
    for rel in ("mica.yaml", "memory/mica.yaml"):
        p = project_root / rel
        if p.exists():
            return p
    return None


def find_legacy_archive(project_root: Path) -> Path | None:
    memory_dir = project_root / "memory"
    if not memory_dir.exists():
        return None
    matches = sorted(memory_dir.glob("*.mica.*.json"))
    return max(matches, key=_legacy_archive_sort_key) if matches else None


def _parse_version(v: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", str(v))
    return tuple(int(x) for x in parts) if parts else (0,)


def layer_label(layer: dict[str, Any]) -> str:
    for field in ("name", "id", "kind"):
        value = layer.get(field)
        if _is_non_empty_string(value):
            return str(value)
    return ""


def layer_role(layer: dict[str, Any]) -> str:
    for field in ("kind", "name"):
        value = layer.get(field)
        if _is_non_empty_string(value):
            return str(value)
    return ""


_INVOKED_LOADING_HINTS = frozenset({"always", "session_start_only"})
_AGENT_CONTEXT_ROLE_ORDER = ("archive", "playbook", "slots", "lessons", "memories")
_AGENT_CONTEXT_ALLOWED_SURFACES = frozenset(_AGENT_CONTEXT_ROLE_ORDER)
_OPERATOR_ONLY_ALLOWED_SURFACES = frozenset(
    (
        "archive",
        "playbook",
        "lessons",
        "sessions",
        "observations",
        "memories",
        "recall",
        "candidates",
        "slots",
        "graph",
    )
)


def _mode_default_surfaces(mode: str) -> list[str]:
    """The pre-profile default: the same surfaces for every session."""
    if mode == "memory_first":
        return ["archive", "playbook", "slots"]
    return ["archive", "playbook"]


def resolve_invocation_contract(yd: dict[str, Any], profile: str | None = None) -> dict[str, Any]:
    """Decide which memory surfaces this session receives.

    This is the selection half of invocation. Before memory profiles it was two
    hardcoded lists keyed on `mode`, which meant every session received the same
    surfaces regardless of what it was for.

    Precedence:
      1. a requested profile from `invocation_protocol.profiles`
      2. `loading_hint: session_start` declared on individual layers
      3. the mode defaults

    A package that declares no profiles resolves exactly as it did before.
    """
    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
    inv = yd.get("invocation_protocol") if isinstance(yd.get("invocation_protocol"), dict) else {}
    raw_agent_context = (
        inv.get("agent_context_surfaces")
        if isinstance(inv.get("agent_context_surfaces"), list)
        else None
    )
    raw_operator_only = (
        inv.get("operator_only_surfaces")
        if isinstance(inv.get("operator_only_surfaces"), list)
        else None
    )
    mode = str(yd.get("mode") or "")
    declared_surfaces: list[str] = []
    invoked_surfaces: list[str] = []
    explicit_invocation = False

    for layer in layers:
        if not isinstance(layer, dict):
            continue
        role = layer_role(layer)
        if not role:
            continue
        declared_surfaces.append(role)
        if layer.get("loading_hint") in _INVOKED_LOADING_HINTS:
            explicit_invocation = True
            invoked_surfaces.append(role)

    profiles = inv.get("profiles") if isinstance(inv.get("profiles"), dict) else {}
    declared_profiles = sorted(str(key) for key in profiles)
    requested_profile = str(profile) if _is_non_empty_string(profile) else None
    active_profile: str | None = None
    unknown_profile: str | None = None
    profile_surfaces: list[str] = []
    undeclared_profile_surfaces: list[str] = []

    if requested_profile is not None:
        if requested_profile in profiles:
            active_profile = requested_profile
        else:
            unknown_profile = requested_profile
    elif "default" in profiles:
        active_profile = "default"

    profile_sections: dict[str, list[str]] = {}
    sections_for_uninvoked_surfaces: list[str] = []
    if active_profile is not None:
        entry = profiles.get(active_profile)
        raw_surfaces = entry.get("surfaces") if isinstance(entry, dict) else None
        if isinstance(raw_surfaces, list):
            profile_surfaces = [
                str(surface) for surface in raw_surfaces if _is_non_empty_string(surface)
            ]
        undeclared_profile_surfaces = [
            role for role in profile_surfaces if role not in declared_surfaces
        ]
        raw_sections = entry.get("sections") if isinstance(entry, dict) else None
        if isinstance(raw_sections, dict):
            for role, names in raw_sections.items():
                if not isinstance(names, list):
                    continue
                wanted = [str(name) for name in names if _is_non_empty_string(name)]
                if wanted:
                    profile_sections[str(role)] = wanted
        sections_for_uninvoked_surfaces = [
            role for role in profile_sections if role not in profile_surfaces
        ]

    if active_profile is not None and profile_surfaces:
        # The profile is the request. What it names is what the session needs.
        invoked_surfaces = [role for role in profile_surfaces if role in declared_surfaces]
        required_session_start = list(profile_surfaces)
    else:
        if not explicit_invocation:
            invoked_surfaces = [
                role for role in _mode_default_surfaces(mode) if role in declared_surfaces
            ]
        required_session_start = _mode_default_surfaces(mode)

    deferred_surfaces = [role for role in declared_surfaces if role not in invoked_surfaces]
    missing_invoked_surfaces = [
        role for role in required_session_start if role not in invoked_surfaces
    ]

    configured_agent_context_surfaces: list[str] = []
    invalid_agent_context_surfaces: list[str] = []
    undeclared_agent_context_surfaces: list[str] = []
    non_invoked_agent_context_surfaces: list[str] = []
    configured_operator_only_surfaces: list[str] = []
    invalid_operator_only_surfaces: list[str] = []
    undeclared_operator_only_surfaces: list[str] = []
    overlapping_operator_only_surfaces: list[str] = []
    if raw_agent_context is not None:
        for surface in raw_agent_context:
            if not _is_non_empty_string(surface):
                continue
            role = str(surface)
            configured_agent_context_surfaces.append(role)
            if role not in _AGENT_CONTEXT_ALLOWED_SURFACES:
                invalid_agent_context_surfaces.append(role)
            elif role not in declared_surfaces:
                undeclared_agent_context_surfaces.append(role)
            elif role not in invoked_surfaces:
                non_invoked_agent_context_surfaces.append(role)
        agent_context_surfaces = [
            role
            for role in configured_agent_context_surfaces
            if role in _AGENT_CONTEXT_ALLOWED_SURFACES and role in invoked_surfaces
        ]
    else:
        agent_context_surfaces = [
            role for role in _AGENT_CONTEXT_ROLE_ORDER if role in invoked_surfaces
        ]
        if not agent_context_surfaces:
            agent_context_surfaces = list(invoked_surfaces)

    if raw_operator_only is not None:
        for surface in raw_operator_only:
            if not _is_non_empty_string(surface):
                continue
            role = str(surface)
            configured_operator_only_surfaces.append(role)
            if role not in _OPERATOR_ONLY_ALLOWED_SURFACES:
                invalid_operator_only_surfaces.append(role)
            elif role not in declared_surfaces:
                undeclared_operator_only_surfaces.append(role)
            elif role in agent_context_surfaces:
                overlapping_operator_only_surfaces.append(role)
        operator_only_surfaces = [
            role
            for role in configured_operator_only_surfaces
            if role in _OPERATOR_ONLY_ALLOWED_SURFACES
            and role in declared_surfaces
            and role not in agent_context_surfaces
        ]
    else:
        operator_only_surfaces = []

    return {
        "invocation_contract": "memory_first" if mode == "memory_first" else "archive_first",
        "declared_profiles": declared_profiles,
        "requested_profile": requested_profile,
        "active_profile": active_profile,
        "unknown_profile": unknown_profile,
        "undeclared_profile_surfaces": undeclared_profile_surfaces,
        "profile_sections": profile_sections,
        "sections_for_uninvoked_surfaces": sections_for_uninvoked_surfaces,
        "declared_surfaces": declared_surfaces,
        "loaded_surfaces": invoked_surfaces,
        "agent_context_surfaces": agent_context_surfaces,
        "operator_only_surfaces": operator_only_surfaces,
        "deferred_surfaces": deferred_surfaces,
        "missing_invoked_surfaces": missing_invoked_surfaces,
        "configured_agent_context_surfaces": configured_agent_context_surfaces,
        "invalid_agent_context_surfaces": invalid_agent_context_surfaces,
        "undeclared_agent_context_surfaces": undeclared_agent_context_surfaces,
        "non_invoked_agent_context_surfaces": non_invoked_agent_context_surfaces,
        "configured_operator_only_surfaces": configured_operator_only_surfaces,
        "invalid_operator_only_surfaces": invalid_operator_only_surfaces,
        "undeclared_operator_only_surfaces": undeclared_operator_only_surfaces,
        "overlapping_operator_only_surfaces": overlapping_operator_only_surfaces,
    }


def _archive_version_key(path: Path, archive: dict[str, Any]) -> tuple[int, ...]:
    project = archive.get("project") if isinstance(archive.get("project"), dict) else {}
    project_version = project.get("version")
    filename_match = re.search(r"\.v(\d+(?:\.\d+)*)\.json$", path.name)

    candidates = []
    if isinstance(project_version, str) and project_version.strip():
        candidates.append(_parse_version(project_version))
    if filename_match:
        candidates.append(_parse_version(filename_match.group(1)))
    return max(candidates, default=(0,))


def _archive_last_updated_key(archive: dict[str, Any]) -> int:
    op_meta = (
        archive.get("operation_meta") if isinstance(archive.get("operation_meta"), dict) else {}
    )
    last_updated = op_meta.get("last_updated")
    if not isinstance(last_updated, str) or not last_updated:
        return -1
    try:
        return date.fromisoformat(last_updated).toordinal()
    except ValueError:
        return -1


def _legacy_archive_sort_key(path: Path) -> tuple[tuple[int, ...], int, int, str]:
    archive = load_json(path)
    return (
        _archive_version_key(path, archive),
        _archive_last_updated_key(archive),
        path.stat().st_mtime_ns,
        path.name,
    )


def run_pct_checks(project_root: Path, profile: str | None = None) -> list[tuple[str, str, str]]:
    """
    Run PCT-001 through PCT-018. Returns list of (id, status, message).

    Only CONTRACT_CHECKS decide CLOSED CONTRACT; ARCHIVE_CHECKS and FLOW_CHECKS
    report on their own axes. `profile` selects a memory profile declared under
    `invocation_protocol.profiles`.
    PCT-011, PCT-012, PCT-014, and PCT-018 remain WARN/INFO-only. PCT-013/014/015/017/018 are flow-gated.
    """
    results: list[tuple[str, str, str]] = []

    mica_yaml_path = find_mica_yaml(project_root)
    if mica_yaml_path:
        results.append(
            ("PCT-001", "PASS", f"mica.yaml present ({mica_yaml_path.relative_to(project_root)})")
        )
    else:
        results.append(("PCT-001", "FAIL", "mica.yaml missing (checked root + memory/)"))
        results.append(("PCT-009", "FAIL", "package incomplete. failing checks: ['PCT-001']"))
        return results

    try:
        yd = load_yaml(mica_yaml_path)
    except Exception as exc:
        results.append(("PCT-002", "FAIL", f"mica.yaml parse error: {exc}"))
        results.append(("PCT-009", "FAIL", "package incomplete. failing checks: ['PCT-002']"))
        return results

    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
    layer_roles = [layer_role(lyr) for lyr in layers if isinstance(lyr, dict)]
    valid_modes = {"memory_injection", "protocol_evolution", "memory_first"}
    di_policy = yd.get("di_policy", {}) if isinstance(yd.get("di_policy"), dict) else {}
    critical_binding_required = bool(di_policy.get("critical_binding_required", False))
    flow_policy = yd.get("flow_policy", {}) if isinstance(yd.get("flow_policy"), dict) else {}
    recall_policy = yd.get("recall_policy", {}) if isinstance(yd.get("recall_policy"), dict) else {}

    required_fields = {"mica_spec", "mode", "layers"}
    missing = required_fields - set(yd.keys())
    if missing:
        results.append(("PCT-002", "FAIL", f"missing required fields: {sorted(missing)}"))
    elif "archive" not in layer_roles:
        results.append(("PCT-002", "FAIL", "archive layer missing"))
    elif "playbook" not in layer_roles:
        results.append(("PCT-002", "FAIL", "playbook layer missing"))
    elif yd.get("mode") not in valid_modes:
        results.append(("PCT-002", "FAIL", f"invalid mode: {yd.get('mode')}"))
    else:
        results.append(("PCT-002", "PASS", "required fields valid"))

    missing_paths = [
        lyr.get("path")
        for lyr in layers
        if isinstance(lyr, dict)
        and lyr.get("required", True)
        and isinstance(lyr.get("path"), str)
        and not (project_root / lyr["path"]).exists()
    ]
    if missing_paths:
        results.append(("PCT-003", "FAIL", f"missing layer paths: {missing_paths}"))
    else:
        results.append(("PCT-003", "PASS", "all required layer paths exist"))

    mode = yd.get("mode", "")
    layer_role_set = set(layer_roles)
    if mode == "memory_injection" and {"archive", "playbook"} <= layer_role_set:
        results.append(("PCT-004", "PASS", "memory_injection coherence ok"))
    elif mode == "protocol_evolution" and {"archive", "playbook", "lessons"} <= layer_role_set:
        results.append(("PCT-004", "PASS", "protocol_evolution coherence ok"))
    elif mode == "protocol_evolution":
        results.append(("PCT-004", "FAIL", "protocol_evolution requires lessons layer"))
    elif (
        mode == "memory_first"
        and {
            "archive",
            "playbook",
            "sessions",
            "observations",
            "memories",
            "slots",
        }
        <= layer_role_set
    ):
        results.append(("PCT-004", "PASS", "memory_first coherence ok"))
    elif mode == "memory_first":
        results.append(
            (
                "PCT-004",
                "FAIL",
                "memory_first requires archive, playbook, sessions, observations, memories, and slots layers",
            )
        )
    else:
        results.append(("PCT-004", "FAIL", f"mode={mode} incompatible with layers={layer_roles}"))

    archive_rel = next(
        (
            lyr.get("path")
            for lyr in layers
            if isinstance(lyr, dict) and layer_role(lyr) == "archive"
        ),
        None,
    )
    archive: dict[str, Any] = {}
    if isinstance(archive_rel, str):
        archive = load_json(project_root / archive_rel)

    if "mica_spec" in archive:
        results.append(("PCT-005", "INFO", f"archive mica_spec = {archive['mica_spec']}"))
    else:
        results.append(("PCT-005", "INFO", "archive mica_spec absent (legacy-valid)"))

    yaml_spec = str(yd.get("mica_spec", ""))
    arch_spec = str(archive.get("mica_spec", ""))
    if yaml_spec and arch_spec and yaml_spec == arch_spec:
        results.append(("PCT-006", "PASS", f"mica_spec aligned: {yaml_spec}"))
    elif yaml_spec and arch_spec:
        results.append(("PCT-006", "WARN", f"drift: mica.yaml={yaml_spec} archive={arch_spec}"))
    else:
        results.append(("PCT-006", "INFO", "mica_spec absent in one or both files"))

    # v0.2.8: warn when declared spec is >= 2 patch versions behind canonical
    # MICA uses 0.MAJOR.PATCH increments; compare the full numeric value.
    declared_spec = yaml_spec or arch_spec
    if declared_spec:
        can = _parse_version(MICA_CANONICAL_VERSION)
        dec = _parse_version(declared_spec)
        if len(can) >= 3 and len(dec) >= 3:
            can_n = can[0] * 10000 + can[1] * 100 + can[2]
            dec_n = dec[0] * 10000 + dec[1] * 100 + dec[2]
            lag = can_n - dec_n
            if lag >= 2:
                results.append(
                    (
                        "PCT-006",
                        "WARN",
                        f"mica_spec {declared_spec} is {lag} version(s) behind "
                        f"canonical {MICA_CANONICAL_VERSION} -- consider upgrading",
                    )
                )

    inv = yd.get("invocation_protocol") if isinstance(yd.get("invocation_protocol"), dict) else {}
    pattern = inv.get("primary_pattern") if isinstance(inv.get("primary_pattern"), str) else None
    contract = resolve_invocation_contract(yd, profile)
    invoked_surfaces = contract["loaded_surfaces"]
    context_surfaces = contract["agent_context_surfaces"]
    missing_invoked_surfaces = contract["missing_invoked_surfaces"]
    invalid_context_surfaces = contract["invalid_agent_context_surfaces"]
    undeclared_context_surfaces = contract["undeclared_agent_context_surfaces"]
    non_invoked_context_surfaces = contract["non_invoked_agent_context_surfaces"]
    operator_only_surfaces = contract["operator_only_surfaces"]
    invalid_operator_only_surfaces = contract["invalid_operator_only_surfaces"]
    undeclared_operator_only_surfaces = contract["undeclared_operator_only_surfaces"]
    overlapping_operator_only_surfaces = contract["overlapping_operator_only_surfaces"]
    invoked_label = ", ".join(invoked_surfaces) if invoked_surfaces else "none"
    context_label = ", ".join(context_surfaces) if context_surfaces else "none"
    operator_label = ", ".join(operator_only_surfaces) if operator_only_surfaces else "none"
    valid_patterns = {
        "readme_protocol",
        "hook_trigger",
        "agent_yaml_bootstrap",
        "global_skill",
        "workspace_directive",
        "explicit",
    }
    context_config_issues: list[str] = []
    if invalid_context_surfaces:
        context_config_issues.append(f"invalid agent_context surfaces {invalid_context_surfaces}")
    if undeclared_context_surfaces:
        context_config_issues.append(
            f"agent_context surfaces not declared as layers {undeclared_context_surfaces}"
        )
    if non_invoked_context_surfaces:
        context_config_issues.append(
            f"agent_context surfaces not session-start invoked {non_invoked_context_surfaces}"
        )
    operator_config_issues: list[str] = []
    if invalid_operator_only_surfaces:
        operator_config_issues.append(
            f"invalid operator_only surfaces {invalid_operator_only_surfaces}"
        )
    if undeclared_operator_only_surfaces:
        operator_config_issues.append(
            f"operator_only surfaces not declared as layers {undeclared_operator_only_surfaces}"
        )
    if overlapping_operator_only_surfaces:
        operator_config_issues.append(
            f"operator_only surfaces overlap agent_context {overlapping_operator_only_surfaces}"
        )
    profile_config_issues: list[str] = []
    if contract["unknown_profile"]:
        profile_config_issues.append(
            f"requested memory profile {contract['unknown_profile']!r} is not declared "
            f"(available: {contract['declared_profiles'] or 'none'})"
        )
    if contract["undeclared_profile_surfaces"]:
        profile_config_issues.append(
            f"memory profile {contract['active_profile']!r} names surfaces that are not "
            f"declared as layers {contract['undeclared_profile_surfaces']}"
        )
    if contract["sections_for_uninvoked_surfaces"]:
        profile_config_issues.append(
            f"memory profile {contract['active_profile']!r} selects sections of surfaces it "
            f"does not invoke {contract['sections_for_uninvoked_surfaces']}"
        )
    for role, wanted in (contract["profile_sections"] or {}).items():
        rel = next(
            (
                lyr.get("path")
                for lyr in layers
                if isinstance(lyr, dict) and layer_role(lyr) == role
            ),
            None,
        )
        if not isinstance(rel, str):
            continue
        target = project_root / rel
        if not target.is_file():
            continue
        try:
            _, present = parse_markdown_sections(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            profile_config_issues.append(f"cannot read {role} to resolve requested sections")
            continue
        absent = [name for name in wanted if name not in present]
        if absent:
            profile_config_issues.append(
                f"memory profile {contract['active_profile']!r} requests {role} sections that "
                f"do not exist {absent} (available: {sorted(present) or 'none'})"
            )
    invocation_config_issues = (
        profile_config_issues + context_config_issues + operator_config_issues
    )

    if pattern is None:
        if missing_invoked_surfaces:
            results.append(
                (
                    "PCT-007",
                    "FAIL",
                    f"invocation contract incomplete; missing required session-start surfaces {missing_invoked_surfaces} (invoked={invoked_label}; context={context_label})",
                )
            )
        elif invocation_config_issues:
            details = "; ".join(invocation_config_issues)
            results.append(
                (
                    "PCT-007",
                    "FAIL",
                    f"invocation_protocol surface contract invalid: {details} (invoked={invoked_label}; context={context_label}; operator={operator_label})",
                )
            )
        elif isinstance(yd.get("invocation_protocol"), dict):
            results.append(
                (
                    "PCT-007",
                    "WARN",
                    f"primary_pattern omitted; runtime default readme_protocol applies (invoked={invoked_label}; context={context_label}; operator={operator_label})",
                )
            )
        else:
            results.append(
                (
                    "PCT-007",
                    "INFO",
                    f"invocation_protocol absent (default/manual handling); invoked={invoked_label}; context={context_label}; operator={operator_label}",
                )
            )
    elif pattern not in valid_patterns:
        results.append(("PCT-007", "FAIL", f"invalid primary_pattern: {pattern}"))
    elif missing_invoked_surfaces:
        results.append(
            (
                "PCT-007",
                "FAIL",
                f"primary_pattern valid: {pattern}, but invocation contract missing required session-start surfaces {missing_invoked_surfaces} (invoked={invoked_label}; context={context_label})",
            )
        )
    elif invocation_config_issues:
        details = "; ".join(invocation_config_issues)
        results.append(
            (
                "PCT-007",
                "FAIL",
                f"primary_pattern valid: {pattern}, but invocation_protocol surface contract invalid: {details} (invoked={invoked_label}; context={context_label}; operator={operator_label})",
            )
        )
    else:
        results.append(
            (
                "PCT-007",
                "PASS",
                f"primary_pattern valid: {pattern}; invoked={invoked_label}; context={context_label}; operator={operator_label}",
            )
        )

    hook_hint_layers = [
        layer_label(lyr)
        for lyr in layers
        if isinstance(lyr, dict) and lyr.get("loading_hint") == "hook"
    ]
    hook_script = inv.get("hook_script") if isinstance(inv.get("hook_script"), str) else None
    if pattern == "hook_trigger":
        if not hook_script:
            results.append(("PCT-008", "FAIL", "hook_trigger declared without hook_script"))
        elif not (project_root / hook_script).exists():
            results.append(("PCT-008", "FAIL", f"hook_script missing: {hook_script}"))
        else:
            results.append(("PCT-008", "PASS", f"hook_script present: {hook_script}"))
    elif hook_hint_layers:
        results.append(
            (
                "PCT-008",
                "WARN",
                f"loading_hint=hook used without hook_trigger on {hook_hint_layers}",
            )
        )
    else:
        results.append(("PCT-008", "INFO", "no hook-specific coherence issues"))

    if archive:
        dis = [d for d in archive.get("design_invariants", []) if isinstance(d, dict)]
        critical_dis = [d for d in dis if d.get("severity") == "critical"]
        unbound = [
            d.get("id", "?")
            for d in critical_dis
            if not isinstance(d.get("binding"), dict) or not d["binding"].get("origin_episode")
        ]
        if not critical_dis:
            results.append(("PCT-010", "INFO", "no critical DIs in archive"))
        elif unbound:
            if critical_binding_required:
                results.append(
                    (
                        "PCT-010",
                        "FAIL",
                        f"critical DIs missing binding.origin_episode: {unbound}"
                        f" -- di_policy.critical_binding_required is true",
                    )
                )
            else:
                results.append(
                    (
                        "PCT-010",
                        "WARN",
                        f"critical DIs missing binding.origin_episode: {unbound}"
                        f" -- set di_policy.critical_binding_required: true to escalate to FAIL",
                    )
                )
        else:
            results.append(
                ("PCT-010", "PASS", f"all {len(critical_dis)} critical DIs have binding")
            )

        # v0.2.8: doctrinal binding quality check (applies to all bound critical DIs)
        doctrinal_ids = [
            d.get("id", "?")
            for d in critical_dis
            if isinstance(d.get("binding"), dict)
            and d["binding"].get("origin_episode")
            and not any(p.search(d["binding"]["origin_episode"]) for p in _EPISODE_PATTERNS)
        ]
        if doctrinal_ids:
            results.append(
                (
                    "PCT-010",
                    "WARN",
                    f"doctrinal binding (no episode code, version ref, or date): "
                    f"{doctrinal_ids} -- ground origin_episode in a real incident",
                )
            )

        # v0.2.8: violation_count / last_triggered coherence
        incoherent_ids = [
            d.get("id", "?")
            for d in critical_dis
            if isinstance(d.get("binding"), dict)
            and d["binding"].get("violation_count", 0)
            and not d["binding"].get("last_triggered")
        ]
        if incoherent_ids:
            results.append(
                (
                    "PCT-010",
                    "WARN",
                    f"violation_count > 0 but last_triggered empty: {incoherent_ids}",
                )
            )

        broken_refs = [
            (d.get("id", "?"), d["binding"]["lesson_ref"])
            for d in critical_dis
            if isinstance(d.get("binding"), dict)
            and isinstance(d["binding"].get("lesson_ref"), str)
            and d["binding"]["lesson_ref"]
            and not (project_root / d["binding"]["lesson_ref"]).exists()
        ]
        if broken_refs:
            results.append(("PCT-011", "WARN", f"binding.lesson_ref dead links: {broken_refs}"))
        else:
            bound_with_ref = [
                d
                for d in critical_dis
                if isinstance(d.get("binding"), dict) and d["binding"].get("lesson_ref")
            ]
            if bound_with_ref:
                results.append(
                    ("PCT-011", "PASS", f"all {len(bound_with_ref)} lesson_ref paths exist")
                )
            else:
                results.append(
                    ("PCT-011", "INFO", "no lesson_ref fields declared; nothing to validate")
                )
    else:
        results.append(("PCT-010", "INFO", "archive not loaded; binding check skipped"))
        results.append(("PCT-011", "INFO", "archive not loaded; lesson_ref check skipped"))

    # PCT-012: archive freshness (v0.2.8, opt-in via di_policy.max_archive_age_days)
    max_age_days = di_policy.get("max_archive_age_days")
    if isinstance(max_age_days, int) and max_age_days > 0 and archive:
        op_meta = archive.get("operation_meta") or {}
        last_updated = op_meta.get("last_updated", "")
        if last_updated:
            try:
                lu = date.fromisoformat(str(last_updated))
                age = (date.today() - lu).days
                if age > max_age_days:
                    results.append(
                        (
                            "PCT-012",
                            "WARN",
                            f"archive last_updated {last_updated} is {age} days old "
                            f"(max_archive_age_days={max_age_days})",
                        )
                    )
                else:
                    results.append(
                        (
                            "PCT-012",
                            "PASS",
                            f"archive last_updated {last_updated} is {age} days old "
                            f"(within {max_age_days}-day limit)",
                        )
                    )
            except ValueError:
                results.append(
                    (
                        "PCT-012",
                        "WARN",
                        f"operation_meta.last_updated '{last_updated}' is not a valid ISO date",
                    )
                )
        else:
            results.append(
                (
                    "PCT-012",
                    "WARN",
                    "max_archive_age_days set but operation_meta.last_updated absent in archive",
                )
            )
    else:
        results.append(
            (
                "PCT-012",
                "INFO",
                "archive freshness check not configured "
                "(set di_policy.max_archive_age_days to enable)",
            )
        )

    from mica_flow import (
        _run_pct013,
        _run_pct014,
        _run_pct015,
        _run_pct017,
        _run_pct018,
    )

    results.append(_run_pct013(project_root, flow_policy))
    results.append(_run_pct014(project_root, flow_policy, recall_policy))
    results.append(_run_pct015(project_root, flow_policy))
    results.append(_run_pct018(project_root, flow_policy))
    results.append(_run_pct017(project_root, flow_policy, recall_policy))

    fails = [r[0] for r in results if r[1] == "FAIL" and r[0] in CONTRACT_CHECKS]
    if fails:
        results.append(("PCT-009", "FAIL", f"invocation contract incomplete: {fails}"))
    else:
        results.append(
            ("PCT-009", "PASS", "declared memory surfaces reached the session; contract closed")
        )

    return results


def is_closed_contract(results: list[tuple[str, str, str]]) -> bool:
    return not any(r[1] == "FAIL" and r[0] in CONTRACT_CHECKS for r in results)


def _axis_state(results: list[tuple[str, str, str]], members: frozenset[str]) -> str:
    """Summarize one verdict axis as FAILED / ISSUES / OK / N-A."""
    seen = [(status, pid) for pid, status, _ in results if pid in members]
    if not seen:
        return "N/A"
    if any(status == "FAIL" for status, _ in seen):
        return "FAILED"
    if any(status == "WARN" for status, _ in seen):
        return "ISSUES"
    if all(status == "INFO" for status, _ in seen):
        return "N/A"
    return "OK"


def evaluate_axes(results: list[tuple[str, str, str]]) -> dict[str, str]:
    """Report the three concerns separately.

    Collapsing them into one verdict is what let archive quality and pipeline
    integrity fail a package whose memory loaded correctly.
    """
    return {
        "contract": "CLOSED" if is_closed_contract(results) else "INCOMPLETE",
        "archive": _axis_state(results, ARCHIVE_CHECKS),
        "flow": _axis_state(results, FLOW_CHECKS),
    }


def failing_axes(results: list[tuple[str, str, str]]) -> list[str]:
    """Axes carrying a FAIL. Used by --strict to widen the exit code."""
    axes = evaluate_axes(results)
    failing = []
    if axes["contract"] == "INCOMPLETE":
        failing.append("contract")
    if axes["archive"] == "FAILED":
        failing.append("archive")
    if axes["flow"] == "FAILED":
        failing.append("flow")
    return failing


# --- evidence facade --------------------------------------------------------
#
# Vocabulary constants are re-exported eagerly; mica_evidence does not import
# them back, so this does not create a cycle.
from mica_evidence import (  # noqa: E402,F401
    DELIVERY_STATES as DELIVERY_STATES,
)
from mica_evidence import (  # noqa: E402,F401
    INVOCATION_SCHEMA_V1 as INVOCATION_SCHEMA_V1,
)
from mica_evidence import (  # noqa: E402,F401
    INVOCATION_SCHEMA_V2 as INVOCATION_SCHEMA_V2,
)
from mica_evidence import (  # noqa: E402,F401
    SURFACE_AUDIENCES as SURFACE_AUDIENCES,
)

#
# The implementations live in mica_evidence. These thin delegations keep
# `from mica_core import ...` working for consumer packages that vendored an
# earlier tools/ copy, while the import stays local so mica_evidence can import
# its primitives from here without a cycle.


def compute_capsule_hash(record: dict[str, Any]) -> str:
    from mica_evidence import compute_capsule_hash as _impl

    return _impl(record)


def run_invocation_trace_checks(target: Path) -> list[tuple[str, str, str]]:
    from mica_evidence import run_invocation_trace_checks as _impl

    return _impl(target)


def rehash_evidence_entry(project_root: Path, entry: dict[str, Any]) -> tuple[str, int] | str:
    from mica_evidence import rehash_evidence_entry as _impl

    return _impl(project_root, entry)
