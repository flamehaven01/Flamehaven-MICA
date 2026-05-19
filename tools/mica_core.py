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
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HARD_FAIL_CHECKS = frozenset(
    {"PCT-001", "PCT-002", "PCT-003", "PCT-004", "PCT-007", "PCT-008", "PCT-010"}
)


# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import]

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except ImportError:
        pass
    return _minimal_yaml_parse(path)


def _coerce(val: str) -> Any:
    if val.lower() in ("true", "yes", "on"):
        return True
    if val.lower() in ("false", "no", "off"):
        return False
    if val.lower() in ("null", "none", "~"):
        return None
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def _tokenize(path: Path) -> list[tuple[int, str]]:
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.lstrip()
        if s and not s.startswith("#"):
            result.append((len(line) - len(s), s))
    return result


def _parse_block(
    tokens: list[tuple[int, str]], pos: int, min_indent: int
) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while pos < len(tokens):
        indent, content = tokens[pos]
        if indent < min_indent:
            break
        if content.startswith("- ") or ":" not in content:
            pos += 1
            continue
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip().strip('"').strip("'")
        pos += 1
        if rest:
            result[key] = _coerce(rest)
        elif pos < len(tokens) and tokens[pos][0] > indent:
            next_indent, next_content = tokens[pos]
            if next_content.startswith("- "):
                val, pos = _parse_list(tokens, pos, next_indent)
                result[key] = val
            else:
                val, pos = _parse_block(tokens, pos, next_indent)
                result[key] = val
        else:
            result[key] = None
    return result, pos


def _parse_list(tokens: list[tuple[int, str]], pos: int, item_indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while pos < len(tokens):
        indent, content = tokens[pos]
        if indent < item_indent or not content.startswith("- "):
            break
        inner = content[2:].strip()
        pos += 1
        if not inner:
            result.append(None)
            continue
        if ":" in inner:
            k, _, v = inner.partition(":")
            item: Any = {k.strip(): _coerce(v.strip().strip('"').strip("'"))}
            if pos < len(tokens) and tokens[pos][0] > indent:
                extra, pos = _parse_block(tokens, pos, tokens[pos][0])
                item.update(extra)
        else:
            item = _coerce(inner.strip('"').strip("'"))
        result.append(item)
    return result, pos


def _minimal_yaml_parse(path: Path) -> dict[str, Any]:
    """
    Best-effort YAML parser for MICA mica.yaml.
    Handles: top-level keys, nested dicts (unlimited depth), lists of dicts.
    Does NOT handle: anchors, tags, multi-line strings, flow syntax {}/{}.
    Install PyYAML for full YAML support: pip install pyyaml
    """
    tokens = _tokenize(path)
    result, _ = _parse_block(tokens, 0, 0)
    return result


# ---------------------------------------------------------------------------
# Package resolution
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
    return matches[0] if matches else None


def load_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# PCT checks
# ---------------------------------------------------------------------------


def run_pct_checks(project_root: Path) -> list[tuple[str, str, str]]:
    """
    Run PCT-001 through PCT-011. Returns list of (id, status, message).
    Hard-fail checks: PCT-001, 002, 003, 004, 007, 008.
    PCT-010 and PCT-011 are WARN-only and do not break CLOSED CONTRACT.
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
    layer_names = [lyr.get("name", "") for lyr in layers if isinstance(lyr, dict)]
    valid_modes = {"memory_injection", "protocol_evolution"}
    di_policy = yd.get("di_policy", {}) if isinstance(yd.get("di_policy"), dict) else {}
    critical_binding_required = bool(di_policy.get("critical_binding_required", False))

    required_fields = {"mica_spec", "mode", "layers"}
    missing = required_fields - set(yd.keys())
    if missing:
        results.append(("PCT-002", "FAIL", f"missing required fields: {sorted(missing)}"))
    elif "archive" not in layer_names:
        results.append(("PCT-002", "FAIL", "archive layer missing"))
    elif "playbook" not in layer_names:
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
    if mode == "memory_injection" and {"archive", "playbook"} <= set(layer_names):
        results.append(("PCT-004", "PASS", "memory_injection coherence ok"))
    elif mode == "protocol_evolution" and {"archive", "playbook", "lessons"} <= set(layer_names):
        results.append(("PCT-004", "PASS", "protocol_evolution coherence ok"))
    elif mode == "protocol_evolution":
        results.append(("PCT-004", "FAIL", "protocol_evolution requires lessons layer"))
    else:
        results.append(("PCT-004", "FAIL", f"mode={mode} incompatible with layers={layer_names}"))

    archive_rel = next(
        (
            lyr.get("path")
            for lyr in layers
            if isinstance(lyr, dict) and lyr.get("name") == "archive"
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

    inv = yd.get("invocation_protocol") if isinstance(yd.get("invocation_protocol"), dict) else {}
    pattern = inv.get("primary_pattern") if isinstance(inv.get("primary_pattern"), str) else None
    valid_patterns = {
        "readme_protocol",
        "hook_trigger",
        "agent_yaml_bootstrap",
        "global_skill",
        "workspace_directive",
        "explicit",
    }
    if pattern is None:
        results.append(("PCT-007", "INFO", "invocation_protocol absent (default/manual handling)"))
    elif pattern not in valid_patterns:
        results.append(("PCT-007", "FAIL", f"invalid primary_pattern: {pattern}"))
    else:
        results.append(("PCT-007", "PASS", f"primary_pattern valid: {pattern}"))

    hook_hint_layers = [
        lyr.get("name")
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

    fails = [r[0] for r in results if r[1] == "FAIL" and r[0] in HARD_FAIL_CHECKS]
    if fails:
        results.append(("PCT-009", "FAIL", f"package incomplete. failing checks: {fails}"))
    else:
        results.append(("PCT-009", "PASS", "package complete. closed contract verified."))

    return results


def is_closed_contract(results: list[tuple[str, str, str]]) -> bool:
    return not any(r[1] == "FAIL" and r[0] in HARD_FAIL_CHECKS for r in results)
