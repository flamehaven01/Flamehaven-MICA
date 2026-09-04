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
from dataclasses import dataclass
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
from mica_primitives import (
    validate_against_schema as validate_against_schema,
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
_AGENT_CONTEXT_ROLE_ORDER = ("archive", "playbook", "handoff", "slots", "lessons", "memories")
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
        "handoff",
    )
)


def _mode_default_surfaces(mode: str) -> list[str]:
    """The pre-profile default: the same surfaces for every session."""
    if mode == "memory_first":
        return ["archive", "playbook", "slots"]
    return ["archive", "playbook"]


def _surface_family(role: str) -> str:
    """The canonical surface that a specialised role belongs to.

    A package that keeps several playbooks apart names them `playbook-eqa`,
    `playbook-bav`. Those are distinct surfaces when a profile selects one, but
    for audience purposes they are playbooks. The qualifier after the first
    hyphen narrows a surface; it never moves it to a different audience, so
    `sessions-2024` stays out of agent context exactly as `sessions` does.
    """
    return role.split("-", 1)[0]


def _is_audience_eligible(role: str, allowed: frozenset[str]) -> bool:
    return role in allowed or _surface_family(role) in allowed


def _classify_surface(
    role: str,
    allowed: frozenset[str],
    declared_surfaces: list[str],
    invoked_surfaces: list[str],
) -> str | None:
    """Why this surface cannot be honoured, or None if it can.

    Returning a reason instead of appending into one of several lists is what
    flattens the caller: the branching lives here, at depth 1.
    """
    if not _is_audience_eligible(role, allowed):
        return "invalid"
    if role not in declared_surfaces:
        return "undeclared"
    if role not in invoked_surfaces:
        return "non_invoked"
    return None


def _declared_roles(raw: list[Any] | None) -> list[str]:
    return [str(s) for s in (raw or []) if _is_non_empty_string(s)]


def _resolve_agent_context_surfaces(
    raw_agent_context: list[Any] | None,
    declared_surfaces: list[str],
    invoked_surfaces: list[str],
) -> dict[str, list[str]]:
    """Validate the declared agent_context surfaces against what was invoked."""
    if raw_agent_context is None:
        # No declaration: fall back to the canonical role order.
        surfaces = [role for role in _AGENT_CONTEXT_ROLE_ORDER if role in invoked_surfaces]
        return {
            "agent_context_surfaces": surfaces or list(invoked_surfaces),
            "configured_agent_context_surfaces": [],
            "invalid_agent_context_surfaces": [],
            "undeclared_agent_context_surfaces": [],
            "non_invoked_agent_context_surfaces": [],
        }

    configured = _declared_roles(raw_agent_context)
    faults: dict[str, list[str]] = {"invalid": [], "undeclared": [], "non_invoked": []}
    for role in configured:
        reason = _classify_surface(
            role, _AGENT_CONTEXT_ALLOWED_SURFACES, declared_surfaces, invoked_surfaces
        )
        if reason:
            faults[reason].append(role)
    return {
        "agent_context_surfaces": [
            role
            for role in configured
            if _is_audience_eligible(role, _AGENT_CONTEXT_ALLOWED_SURFACES)
            and role in invoked_surfaces
        ],
        "configured_agent_context_surfaces": configured,
        "invalid_agent_context_surfaces": faults["invalid"],
        "undeclared_agent_context_surfaces": faults["undeclared"],
        "non_invoked_agent_context_surfaces": faults["non_invoked"],
    }


def _resolve_operator_only_surfaces(
    raw_operator_only: list[Any] | None,
    declared_surfaces: list[str],
    agent_context_surfaces: list[str],
) -> dict[str, list[str]]:
    """Validate operator_only surfaces and keep them out of agent context."""
    if raw_operator_only is None:
        return {
            "operator_only_surfaces": [],
            "configured_operator_only_surfaces": [],
            "invalid_operator_only_surfaces": [],
            "undeclared_operator_only_surfaces": [],
            "overlapping_operator_only_surfaces": [],
        }

    configured = _declared_roles(raw_operator_only)
    invalid = [
        r for r in configured if not _is_audience_eligible(r, _OPERATOR_ONLY_ALLOWED_SURFACES)
    ]
    undeclared = [
        r
        for r in configured
        if _is_audience_eligible(r, _OPERATOR_ONLY_ALLOWED_SURFACES) and r not in declared_surfaces
    ]
    overlapping = [
        r
        for r in configured
        if r in _OPERATOR_ONLY_ALLOWED_SURFACES
        and r in declared_surfaces
        and r in agent_context_surfaces
    ]
    return {
        "operator_only_surfaces": [
            r
            for r in configured
            if r in _OPERATOR_ONLY_ALLOWED_SURFACES
            and r in declared_surfaces
            and r not in agent_context_surfaces
        ],
        "configured_operator_only_surfaces": configured,
        "invalid_operator_only_surfaces": invalid,
        "undeclared_operator_only_surfaces": undeclared,
        "overlapping_operator_only_surfaces": overlapping,
    }


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
    duplicate_surface_roles: list[str] = []
    invoked_surfaces: list[str] = []
    role_loading_hints: dict[str, str] = {}
    explicit_invocation = False

    for layer in layers:
        if not isinstance(layer, dict):
            continue
        role = layer_role(layer)
        if not role:
            continue
        if role in declared_surfaces:
            duplicate_surface_roles.append(role)
        declared_surfaces.append(role)
        hint = layer.get("loading_hint")
        role_loading_hints[role] = str(hint) if _is_non_empty_string(hint) else "unset"
        if hint in _INVOKED_LOADING_HINTS:
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
    malformed_profile: str | None = None
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
        if isinstance(raw_surfaces, list) and not profile_surfaces:
            # An empty surface list is a declaration that resolves to nothing.
            # Falling back to the mode defaults would silently ignore the
            # operator's request.
            malformed_profile = f"{active_profile!r} declares no usable surfaces"
        elif len(set(profile_surfaces)) != len(profile_surfaces):
            duplicates = sorted({r for r in profile_surfaces if profile_surfaces.count(r) > 1})
            malformed_profile = f"{active_profile!r} repeats surfaces {duplicates}"
        elif not isinstance(raw_surfaces, list):
            malformed_profile = f"{active_profile!r} has no surfaces list"
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

    # The selection basis: which mechanism left this surface out, not just its
    # name. A bare name list lets someone see what was omitted; it does not let
    # anyone later ask whether omitting it mattered. That question needs real
    # sessions with a control -- this only preserves what would be needed to ask
    # it: which rule did the deferring, and what the surface itself declared.
    deferred_surfaces_basis: dict[str, str] = {}
    for role in deferred_surfaces:
        hint = role_loading_hints.get(role, "unset")
        if active_profile is not None and profile_surfaces:
            deferred_surfaces_basis[role] = (
                f"profile {active_profile!r} does not name this surface (loading_hint={hint})"
            )
        elif explicit_invocation:
            deferred_surfaces_basis[role] = (
                f"loading_hint={hint} does not trigger session-start invocation"
            )
        else:
            deferred_surfaces_basis[role] = (
                f"mode {mode!r} default surfaces do not include this role (loading_hint={hint})"
            )

    context = _resolve_agent_context_surfaces(
        raw_agent_context, declared_surfaces, invoked_surfaces
    )
    # agent_context_surfaces is a ceiling -- what may reach the agent at all --
    # not a manifest of what every session gets. Before profiles the two were
    # the same thing, so a permitted surface that was not invoked meant a broken
    # promise. Once a profile does the selecting, the same gap is just a surface
    # this session did not ask for.
    deselected_agent_context_surfaces: list[str] = []
    if active_profile is not None and profile_surfaces:
        deselected_agent_context_surfaces = context["non_invoked_agent_context_surfaces"]
        context["non_invoked_agent_context_surfaces"] = []
    agent_context_surfaces = context["agent_context_surfaces"]
    operator = _resolve_operator_only_surfaces(
        raw_operator_only, declared_surfaces, agent_context_surfaces
    )

    return {
        "invocation_contract": "memory_first" if mode == "memory_first" else "archive_first",
        "declared_profiles": declared_profiles,
        "requested_profile": requested_profile,
        "active_profile": active_profile,
        "unknown_profile": unknown_profile,
        "undeclared_profile_surfaces": undeclared_profile_surfaces,
        "malformed_profile": malformed_profile,
        "profile_sections": profile_sections,
        "sections_for_uninvoked_surfaces": sections_for_uninvoked_surfaces,
        "declared_surfaces": declared_surfaces,
        "duplicate_surface_roles": sorted(set(duplicate_surface_roles)),
        "loaded_surfaces": invoked_surfaces,
        "agent_context_surfaces": agent_context_surfaces,
        "deselected_agent_context_surfaces": deselected_agent_context_surfaces,
        "operator_only_surfaces": operator["operator_only_surfaces"],
        "deferred_surfaces": deferred_surfaces,
        "deferred_surfaces_basis": deferred_surfaces_basis,
        "missing_invoked_surfaces": missing_invoked_surfaces,
        "configured_agent_context_surfaces": context["configured_agent_context_surfaces"],
        "invalid_agent_context_surfaces": context["invalid_agent_context_surfaces"],
        "undeclared_agent_context_surfaces": context["undeclared_agent_context_surfaces"],
        "non_invoked_agent_context_surfaces": context["non_invoked_agent_context_surfaces"],
        "configured_operator_only_surfaces": operator["configured_operator_only_surfaces"],
        "invalid_operator_only_surfaces": operator["invalid_operator_only_surfaces"],
        "undeclared_operator_only_surfaces": operator["undeclared_operator_only_surfaces"],
        "overlapping_operator_only_surfaces": operator["overlapping_operator_only_surfaces"],
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


@dataclass(frozen=True)
class _PackageContext:
    """Package state resolved once, then handed to each check.

    run_pct_checks used to hold all of this as locals in a single 457-line body
    with a cyclomatic complexity of 88. The flow checks had already been split
    into _run_pct013..018; this applies the same shape to PCT-002..012.
    """

    project_root: Path
    profile: str | None
    mica_yaml_path: Path
    yd: dict[str, Any]
    layers: list[Any]
    layer_roles: list[str | None]
    layer_role_set: set[str | None]
    mode: Any
    valid_modes: set[str]
    di_policy: dict[str, Any]
    critical_binding_required: bool
    flow_policy: dict[str, Any]
    recall_policy: dict[str, Any]
    archive: dict[str, Any]
    inv: dict[str, Any]
    pattern: str | None


def _build_package_context(
    project_root: Path, mica_yaml_path: Path, yd: dict[str, Any], profile: str | None
) -> _PackageContext:
    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
    layer_roles = [layer_role(lyr) for lyr in layers if isinstance(lyr, dict)]
    di_policy = yd.get("di_policy", {}) if isinstance(yd.get("di_policy"), dict) else {}
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
    inv = yd.get("invocation_protocol") if isinstance(yd.get("invocation_protocol"), dict) else {}
    return _PackageContext(
        project_root=project_root,
        profile=profile,
        mica_yaml_path=mica_yaml_path,
        yd=yd,
        layers=layers,
        layer_roles=layer_roles,
        layer_role_set=set(layer_roles),
        mode=yd.get("mode", ""),
        valid_modes={"memory_injection", "protocol_evolution", "memory_first"},
        di_policy=di_policy,
        critical_binding_required=bool(di_policy.get("critical_binding_required", False)),
        flow_policy=yd.get("flow_policy", {}) if isinstance(yd.get("flow_policy"), dict) else {},
        recall_policy=(
            yd.get("recall_policy", {}) if isinstance(yd.get("recall_policy"), dict) else {}
        ),
        archive=archive,
        inv=inv,
        pattern=(
            inv.get("primary_pattern") if isinstance(inv.get("primary_pattern"), str) else None
        ),
    )


def _run_pct002(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """Required fields and the archive/playbook layers are declared."""
    out: list[tuple[str, str, str]] = []
    required_fields = {"mica_spec", "mode", "layers"}
    missing = required_fields - set(ctx.yd.keys())
    if missing:
        out.append(("PCT-002", "FAIL", f"missing required fields: {sorted(missing)}"))
    elif "archive" not in ctx.layer_roles:
        out.append(("PCT-002", "FAIL", "archive layer missing"))
    elif "playbook" not in ctx.layer_roles:
        out.append(("PCT-002", "FAIL", "playbook layer missing"))
    elif ctx.yd.get("mode") not in ctx.valid_modes:
        out.append(("PCT-002", "FAIL", f"invalid mode: {ctx.yd.get('mode')}"))
    else:
        out.append(("PCT-002", "PASS", "required fields valid"))
    return out


def _run_pct003(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """Every required layer path resolves to a readable file inside the root.

    Existence alone is not enough. A directory at a declared surface path passed
    this check while producing no evidence, and a path escaping the project root
    would have resolved the same way.
    """
    out: list[tuple[str, str, str]] = []
    unusable: list[str] = []
    # `required: false` exempts a layer from being verified by default. It does
    # not exempt one this session actually asked for: a profile naming a surface
    # is a request, and an unreadable file is a broken request whatever the
    # layer's default says. Without this, an optional surface selected by a
    # profile was skipped here while the runtime reported it missing.
    selected = set(resolve_invocation_contract(ctx.yd, ctx.profile)["loaded_surfaces"])
    for lyr in ctx.layers:
        if not isinstance(lyr, dict):
            continue
        if not lyr.get("required", True) and layer_role(lyr) not in selected:
            continue
        rel = lyr.get("path")
        if not isinstance(rel, str) or not rel.strip():
            # Skipping this let a package delete `path:` from its archive and
            # still close the contract: nothing else in the check chain looks
            # at files, so an unresolvable surface became an invisible one.
            unusable.append(f"{layer_role(lyr) or '<unnamed layer>'} (no usable path declared)")
            continue
        resolved = _resolve_within_root(ctx.project_root, rel)
        if resolved is None:
            unusable.append(f"{rel} (escapes project root)")
        elif resolved.exists() and not resolved.is_file():
            unusable.append(f"{rel} (not a file)")
    if unusable:
        out.append(("PCT-003", "FAIL", f"unusable layer paths: {unusable}"))
        return out
    missing_paths = [
        lyr.get("path")
        for lyr in ctx.layers
        if isinstance(lyr, dict)
        and (lyr.get("required", True) or layer_role(lyr) in selected)
        and isinstance(lyr.get("path"), str)
        and not (ctx.project_root / lyr["path"]).exists()
    ]
    if missing_paths:
        out.append(("PCT-003", "FAIL", f"missing layer paths: {missing_paths}"))
    else:
        out.append(("PCT-003", "PASS", "all required layer paths exist"))
    return out


# Each mode declares the layer roles it cannot operate without. The table
# replaces a six-branch elif chain that mixed mode dispatch with membership
# testing at nesting depth 5.
_MODE_REQUIRED_ROLES: dict[str, frozenset[str]] = {
    "memory_injection": frozenset({"archive", "playbook"}),
    "protocol_evolution": frozenset({"archive", "playbook", "lessons"}),
    "memory_first": frozenset(
        {"archive", "playbook", "sessions", "observations", "memories", "slots"}
    ),
}

_MODE_INCOHERENCE_MESSAGE = {
    "protocol_evolution": "protocol_evolution requires lessons layer",
    "memory_first": (
        "memory_first requires archive, playbook, sessions, observations, "
        "memories, and slots layers"
    ),
}


def _run_pct004(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """The declared mode and the declared layer roles agree."""
    mode = ctx.yd.get("mode", "")
    required = _MODE_REQUIRED_ROLES.get(mode)
    if required is None:
        return [("PCT-004", "FAIL", f"mode={mode} incompatible with layers={ctx.layer_roles}")]
    if required <= set(ctx.layer_roles):
        return [("PCT-004", "PASS", f"{mode} coherence ok")]
    message = _MODE_INCOHERENCE_MESSAGE.get(
        mode, f"mode={mode} incompatible with layers={ctx.layer_roles}"
    )
    return [("PCT-004", "FAIL", message)]


def _run_pct005(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """Report the archive's own mica_spec."""
    out: list[tuple[str, str, str]] = []
    if "mica_spec" in ctx.archive:
        out.append(("PCT-005", "INFO", f"archive mica_spec = {ctx.archive['mica_spec']}"))
    else:
        out.append(("PCT-005", "INFO", "archive mica_spec absent (legacy-valid)"))
    return out


def _run_pct006(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """mica.yaml and archive agree on mica_spec, and it is not far behind canonical."""
    out: list[tuple[str, str, str]] = []
    yaml_spec = str(ctx.yd.get("mica_spec", ""))
    arch_spec = str(ctx.archive.get("mica_spec", ""))
    if yaml_spec and arch_spec and yaml_spec == arch_spec:
        out.append(("PCT-006", "PASS", f"mica_spec aligned: {yaml_spec}"))
    elif yaml_spec and arch_spec:
        out.append(("PCT-006", "WARN", f"drift: mica.yaml={yaml_spec} archive={arch_spec}"))
    else:
        out.append(("PCT-006", "INFO", "mica_spec absent in one or both files"))

    declared_spec = yaml_spec or arch_spec
    if declared_spec:
        out.extend(_spec_lag_result(declared_spec))
    return out


def _spec_lag_result(declared_spec: str) -> list[tuple[str, str, str]]:
    """Compare a declared mica_spec against canonical without inventing a count.

    The original formula packed the version as major*10000 + minor*100 + patch
    and reported the difference as "N version(s) behind". Within one minor that
    is a true patch count, but across a minor boundary it is not a count of
    anything: 0.1.9 against canonical 0.2.8 was reported as "99 versions
    behind". Measuring the live packages surfaced it, since one of them
    declares 0.1.9.

    Patch distance is only stated when the minor matches. Otherwise the gap is
    named without a number.

    The gap is reported, not prescribed. Consumer packages carry their own
    mica.yaml and playbook in their own form and evolve on their own track;
    that divergence is the fleet working as intended, not drift to be
    corrected from the centre. What a maintainer needs from this check is
    which spec their package declares and that the checks here are written
    against canonical. The decision is theirs.
    """
    if not re.search(r"\d", declared_spec):
        return [
            (
                "PCT-006",
                "WARN",
                f"mica_spec {declared_spec!r} contains no version number; "
                f"cannot be compared against canonical {MICA_CANONICAL_VERSION}",
            )
        ]
    can = _parse_version(MICA_CANONICAL_VERSION)
    dec = _parse_version(declared_spec)
    if len(can) < 3 or len(dec) < 3:
        return []

    if dec > can:
        return [
            (
                "PCT-006",
                "WARN",
                f"mica_spec {declared_spec} is ahead of canonical "
                f"{MICA_CANONICAL_VERSION}; no canonical schema exists for it",
            )
        ]
    if dec[0] != can[0]:
        return [
            (
                "PCT-006",
                "WARN",
                f"mica_spec {declared_spec} is behind canonical "
                f"{MICA_CANONICAL_VERSION} by at least one major version; "
                f"the checks here are written against canonical",
            )
        ]
    if dec[:2] != can[:2]:
        return [
            (
                "PCT-006",
                "WARN",
                f"mica_spec {declared_spec} is behind canonical "
                f"{MICA_CANONICAL_VERSION} by at least one minor version; "
                f"the checks here are written against canonical",
            )
        ]
    lag = can[2] - dec[2]
    if lag >= 2:
        return [
            (
                "PCT-006",
                "WARN",
                f"mica_spec {declared_spec} is {lag} patch version(s) behind "
                f"canonical {MICA_CANONICAL_VERSION}; the checks here are "
                f"written against canonical",
            )
        ]
    return []


def handoff_is_deliverable(project_root: Path) -> tuple[bool, str]:
    """Whether a handoff document may enter agent context.

    mica_handoff imports only mica_primitives, so reading it here adds no cycle.
    """
    try:
        import mica_handoff
    except ImportError as exc:  # a partial vendored toolset must fail closed
        return (False, f"handoff validator unavailable: {exc}")

    statuses: dict[str, str] = {}
    messages: dict[str, str] = {}
    for check, status, message in mica_handoff.run_handoff_checks(project_root):
        statuses[check] = status
        messages[check] = message

    if statuses.get("HND-001") == "INFO":
        return (False, "no handoff document present")
    # HND-000 was excluded, so a package whose handoff schema was missing
    # delivered the surface anyway with nothing having validated it.
    for check in ("HND-000", "HND-001", "HND-002", "HND-004", "HND-005"):
        if statuses.get(check) == "FAIL":
            return (False, messages.get(check, f"{check} failed"))
    if statuses.get("HND-003") in {"WARN", "INFO"}:
        return (False, messages.get("HND-003", "handoff is not current"))
    return (True, "valid and current")


def _run_pct007(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """The invocation protocol resolves: pattern, profile, surfaces, audiences."""
    out: list[tuple[str, str, str]] = []
    inv = (
        ctx.yd.get("invocation_protocol")
        if isinstance(ctx.yd.get("invocation_protocol"), dict)
        else {}
    )
    pattern = inv.get("primary_pattern") if isinstance(inv.get("primary_pattern"), str) else None
    contract = resolve_invocation_contract(ctx.yd, ctx.profile)
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
    if contract["duplicate_surface_roles"]:
        # Two layers claiming the same role made the surface ambiguous, and the
        # runtime's path map resolved it by overwriting: the last declaration
        # silently became the evidence, so a decoy file could stand in for the
        # playbook while the contract still closed.
        context_config_issues.append(
            f"surface roles declared more than once {contract['duplicate_surface_roles']}"
        )
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
    # A handoff that fails its own integrity check, or one that has expired or
    # been superseded, is withheld from agent context at runtime. The contract
    # has to agree: a named surface that does not reach the session is not a
    # closed contract, and reporting CLOSED here while the runtime withholds it
    # would make the two disagree about the same session.
    if "handoff" in context_surfaces:
        deliverable, reason = handoff_is_deliverable(ctx.project_root)
        if not deliverable:
            context_config_issues.append(f"handoff named for agent_context but withheld: {reason}")
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
    if contract["malformed_profile"]:
        profile_config_issues.append(f"memory profile {contract['malformed_profile']}")
    if contract["sections_for_uninvoked_surfaces"]:
        profile_config_issues.append(
            f"memory profile {contract['active_profile']!r} selects sections of surfaces it "
            f"does not invoke {contract['sections_for_uninvoked_surfaces']}"
        )
    for role, wanted in (contract["profile_sections"] or {}).items():
        rel = next(
            (
                lyr.get("path")
                for lyr in ctx.layers
                if isinstance(lyr, dict) and layer_role(lyr) == role
            ),
            None,
        )
        if not isinstance(rel, str):
            continue
        target = ctx.project_root / rel
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
            out.append(
                (
                    "PCT-007",
                    "FAIL",
                    f"invocation contract incomplete; missing required session-start surfaces {missing_invoked_surfaces} (invoked={invoked_label}; context={context_label})",
                )
            )
        elif invocation_config_issues:
            details = "; ".join(invocation_config_issues)
            out.append(
                (
                    "PCT-007",
                    "FAIL",
                    f"invocation_protocol surface contract invalid: {details} (invoked={invoked_label}; context={context_label}; operator={operator_label})",
                )
            )
        elif isinstance(ctx.yd.get("invocation_protocol"), dict):
            out.append(
                (
                    "PCT-007",
                    "WARN",
                    f"primary_pattern omitted; runtime default readme_protocol applies (invoked={invoked_label}; context={context_label}; operator={operator_label})",
                )
            )
        else:
            out.append(
                (
                    "PCT-007",
                    "INFO",
                    f"invocation_protocol absent (default/manual handling); invoked={invoked_label}; context={context_label}; operator={operator_label}",
                )
            )
    elif pattern not in valid_patterns:
        out.append(("PCT-007", "FAIL", f"invalid primary_pattern: {pattern}"))
    elif missing_invoked_surfaces:
        out.append(
            (
                "PCT-007",
                "FAIL",
                f"primary_pattern valid: {pattern}, but invocation contract missing required session-start surfaces {missing_invoked_surfaces} (invoked={invoked_label}; context={context_label})",
            )
        )
    elif invocation_config_issues:
        details = "; ".join(invocation_config_issues)
        out.append(
            (
                "PCT-007",
                "FAIL",
                f"primary_pattern valid: {pattern}, but invocation_protocol surface contract invalid: {details} (invoked={invoked_label}; context={context_label}; operator={operator_label})",
            )
        )
    else:
        out.append(
            (
                "PCT-007",
                "PASS",
                f"primary_pattern valid: {pattern}; invoked={invoked_label}; context={context_label}; operator={operator_label}",
            )
        )
    return out


def _run_pct008(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """A declared hook carrier exists."""
    out: list[tuple[str, str, str]] = []
    hook_hint_layers = [
        layer_label(lyr)
        for lyr in ctx.layers
        if isinstance(lyr, dict) and lyr.get("loading_hint") == "hook"
    ]
    hook_script = (
        ctx.inv.get("hook_script") if isinstance(ctx.inv.get("hook_script"), str) else None
    )
    if ctx.pattern == "hook_trigger":
        if not hook_script:
            out.append(("PCT-008", "FAIL", "hook_trigger declared without hook_script"))
        elif not (ctx.project_root / hook_script).exists():
            out.append(("PCT-008", "FAIL", f"hook_script missing: {hook_script}"))
        else:
            out.append(("PCT-008", "PASS", f"hook_script present: {hook_script}"))
    elif hook_hint_layers:
        out.append(
            (
                "PCT-008",
                "WARN",
                f"loading_hint=hook used without hook_trigger on {hook_hint_layers}",
            )
        )
    else:
        out.append(("PCT-008", "INFO", "no hook-specific coherence issues"))
    return out


def _critical_dis(ctx: _PackageContext) -> list[dict[str, Any]]:
    dis = [d for d in ctx.archive.get("design_invariants", []) if isinstance(d, dict)]
    return [d for d in dis if d.get("severity") == "critical"]


def _run_pct010(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """Critical DI binding: present, incident-grounded, and internally coherent."""
    if not ctx.archive:
        return [("PCT-010", "INFO", "archive not loaded; binding check skipped")]

    out: list[tuple[str, str, str]] = []
    critical_dis = _critical_dis(ctx)
    unbound = [
        d.get("id", "?")
        for d in critical_dis
        if not isinstance(d.get("binding"), dict) or not d["binding"].get("origin_episode")
    ]
    if not critical_dis:
        out.append(("PCT-010", "INFO", "no critical DIs in archive"))
    elif unbound and ctx.critical_binding_required:
        out.append(
            (
                "PCT-010",
                "FAIL",
                f"critical DIs missing binding.origin_episode: {unbound}"
                f" -- di_policy.critical_binding_required is true",
            )
        )
    elif unbound:
        out.append(
            (
                "PCT-010",
                "WARN",
                f"critical DIs missing binding.origin_episode: {unbound}"
                f" -- set di_policy.critical_binding_required: true to escalate to FAIL",
            )
        )
    else:
        out.append(("PCT-010", "PASS", f"all {len(critical_dis)} critical DIs have binding"))

    # v0.2.8: an origin_episode with no episode code, version ref, or date
    # restates the label instead of recording what happened.
    doctrinal_ids = [
        d.get("id", "?")
        for d in critical_dis
        if isinstance(d.get("binding"), dict)
        and d["binding"].get("origin_episode")
        and not any(p.search(d["binding"]["origin_episode"]) for p in _EPISODE_PATTERNS)
    ]
    if doctrinal_ids:
        out.append(
            (
                "PCT-010",
                "WARN",
                f"doctrinal binding (no episode code, version ref, or date): "
                f"{doctrinal_ids} -- ground origin_episode in a real incident",
            )
        )

    # v0.2.8: a violation count with no timestamp is an incoherent record.
    incoherent_ids = [
        d.get("id", "?")
        for d in critical_dis
        if isinstance(d.get("binding"), dict)
        and d["binding"].get("violation_count", 0)
        and not d["binding"].get("last_triggered")
    ]
    if incoherent_ids:
        out.append(
            ("PCT-010", "WARN", f"violation_count > 0 but last_triggered empty: {incoherent_ids}")
        )
    return out


def _run_pct011(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """Every declared binding.lesson_ref resolves on disk."""
    if not ctx.archive:
        return [("PCT-011", "INFO", "archive not loaded; lesson_ref check skipped")]

    critical_dis = _critical_dis(ctx)
    broken_refs = [
        (d.get("id", "?"), d["binding"]["lesson_ref"])
        for d in critical_dis
        if isinstance(d.get("binding"), dict)
        and isinstance(d["binding"].get("lesson_ref"), str)
        and d["binding"]["lesson_ref"]
        and not (ctx.project_root / d["binding"]["lesson_ref"]).exists()
    ]
    if broken_refs:
        return [("PCT-011", "WARN", f"binding.lesson_ref dead links: {broken_refs}")]

    bound_with_ref = [
        d
        for d in critical_dis
        if isinstance(d.get("binding"), dict) and d["binding"].get("lesson_ref")
    ]
    if bound_with_ref:
        return [("PCT-011", "PASS", f"all {len(bound_with_ref)} lesson_ref paths exist")]
    return [("PCT-011", "INFO", "no lesson_ref fields declared; nothing to validate")]


def _run_pct012(ctx: _PackageContext) -> list[tuple[str, str, str]]:
    """Archive freshness, when di_policy.max_archive_age_days opts in."""
    out: list[tuple[str, str, str]] = []
    # PCT-012: archive freshness (v0.2.8, opt-in via di_policy.max_archive_age_days)
    max_age_days = ctx.di_policy.get("max_archive_age_days")
    if isinstance(max_age_days, int) and max_age_days > 0 and ctx.archive:
        op_meta = ctx.archive.get("operation_meta") or {}
        last_updated = op_meta.get("last_updated", "")
        if last_updated:
            try:
                lu = date.fromisoformat(str(last_updated))
                age = (date.today() - lu).days
                if age > max_age_days:
                    out.append(
                        (
                            "PCT-012",
                            "WARN",
                            f"archive last_updated {last_updated} is {age} days old "
                            f"(max_archive_age_days={max_age_days})",
                        )
                    )
                else:
                    out.append(
                        (
                            "PCT-012",
                            "PASS",
                            f"archive last_updated {last_updated} is {age} days old "
                            f"(within {max_age_days}-day limit)",
                        )
                    )
            except ValueError:
                out.append(
                    (
                        "PCT-012",
                        "WARN",
                        f"operation_meta.last_updated '{last_updated}' is not a valid ISO date",
                    )
                )
        else:
            out.append(
                (
                    "PCT-012",
                    "WARN",
                    "max_archive_age_days set but operation_meta.last_updated absent in archive",
                )
            )
    else:
        out.append(
            (
                "PCT-012",
                "INFO",
                "archive freshness check not configured "
                "(set di_policy.max_archive_age_days to enable)",
            )
        )
    return out


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
            (
                "PCT-001",
                "PASS",
                f"mica.yaml present ({mica_yaml_path.relative_to(project_root).as_posix()})",
            )
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

    ctx = _build_package_context(project_root, mica_yaml_path, yd, profile)

    for check in (
        _run_pct002,
        _run_pct003,
        _run_pct004,
        _run_pct005,
        _run_pct006,
        _run_pct007,
        _run_pct008,
        _run_pct010,
        _run_pct011,
        _run_pct012,
    ):
        results.extend(check(ctx))

    from mica_flow import (
        _run_pct013,
        _run_pct014,
        _run_pct015,
        _run_pct017,
        _run_pct018,
    )

    results.append(_run_pct013(project_root, ctx.flow_policy))
    results.append(_run_pct014(project_root, ctx.flow_policy, ctx.recall_policy))
    results.append(_run_pct015(project_root, ctx.flow_policy))
    results.append(_run_pct018(project_root, ctx.flow_policy))
    results.append(_run_pct017(project_root, ctx.flow_policy, ctx.recall_policy))

    fails = [r[0] for r in results if r[1] == "FAIL" and r[0] in CONTRACT_CHECKS]
    if fails:
        results.append(("PCT-009", "FAIL", f"invocation contract incomplete: {fails}"))
    else:
        results.append(
            (
                "PCT-009",
                "PASS",
                "declared memory surfaces resolved for this session; contract closed. "
                "Resolution is not delivery -- see IVC-* for recorded invocation evidence",
            )
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
