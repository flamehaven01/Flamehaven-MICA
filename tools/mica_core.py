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

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

HARD_FAIL_CHECKS = frozenset(
    {
        "PCT-001",
        "PCT-002",
        "PCT-003",
        "PCT-004",
        "PCT-007",
        "PCT-008",
        "PCT-010",
        "PCT-013",
        "PCT-015",
        "PCT-017",
    }
)

MICA_CANONICAL_VERSION = "0.2.8"
MICA_TOOL_VERSION = MICA_CANONICAL_VERSION

_OBSERVE_REQUIRED_FIELDS = (
    "schema_version",
    "event_id",
    "timestamp_utc",
    "session_id",
    "hook",
    "scope",
    "summary",
    "redaction",
    "trust_tier",
    "source_system",
    "event_hash",
)

_CANDIDATE_REVIEW_FIELDS = ("reviewed_by", "reviewed_at_utc", "decision_reason")


def format_tool_banner(tool_name: str) -> str:
    return f"{tool_name} v{MICA_TOOL_VERSION}"


# Patterns that mark a real incident-grounded origin_episode.
# Any single match exempts the binding from the doctrinal WARN (v0.2.8).
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
    return max(matches, key=_legacy_archive_sort_key) if matches else None


def _parse_version(v: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", str(v))
    return tuple(int(x) for x in parts) if parts else (0,)


def load_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


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
_AGENT_CONTEXT_ROLE_ORDER = ("archive", "playbook", "slots", "lessons")


def resolve_invocation_contract(yd: dict[str, Any]) -> dict[str, Any]:
    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
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

    if not explicit_invocation:
        defaults = ["archive", "playbook", "slots"] if mode == "memory_first" else ["archive", "playbook"]
        invoked_surfaces = [role for role in defaults if role in declared_surfaces]

    deferred_surfaces = [role for role in declared_surfaces if role not in invoked_surfaces]
    required_session_start = ["archive", "playbook", "slots"] if mode == "memory_first" else ["archive", "playbook"]
    missing_invoked_surfaces = [role for role in required_session_start if role not in invoked_surfaces]
    agent_context_surfaces = [role for role in _AGENT_CONTEXT_ROLE_ORDER if role in invoked_surfaces]
    if not agent_context_surfaces:
        agent_context_surfaces = list(invoked_surfaces)

    return {
        "invocation_contract": "memory_first" if mode == "memory_first" else "archive_first",
        "declared_surfaces": declared_surfaces,
        "loaded_surfaces": invoked_surfaces,
        "agent_context_surfaces": agent_context_surfaces,
        "deferred_surfaces": deferred_surfaces,
        "missing_invoked_surfaces": missing_invoked_surfaces,
    }




def find_flow_artifact(project_root: Path, filename: str) -> Path | None:
    for rel in (filename, f"memory/{filename}"):
        p = project_root / rel
        if p.exists():
            return p
    return None


def load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    result: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError("jsonl record must be an object")
        result.append(data)
    return result


def _normalized_json_text(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_observation_event_hash(record: dict[str, Any]) -> str:
    payload = {k: v for k, v in record.items() if k != "event_hash"}
    digest = hashlib.sha256(_normalized_json_text(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _review_is_approved(review: Any) -> bool:
    if not isinstance(review, dict) or review.get("state") != "approved":
        return False
    return all(_is_non_empty_string(review.get(field)) for field in _CANDIDATE_REVIEW_FIELDS)


def _flow_enabled(flow_policy: dict[str, Any]) -> bool:
    return bool(flow_policy.get("enabled", False))


def _run_pct013(project_root: Path, flow_policy: dict[str, Any]) -> tuple[str, str, str]:
    if not _flow_enabled(flow_policy):
        return ("PCT-013", "INFO", "flow disabled; observation coherence not required")

    observe_path = find_flow_artifact(project_root, "mica.observe.jsonl")
    if not observe_path:
        return ("PCT-013", "FAIL", "flow enabled but mica.observe.jsonl missing")

    records: list[dict[str, Any]] = []
    for lineno, raw in enumerate(observe_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            return ("PCT-013", "FAIL", f"line {lineno} JSON parse error: {exc.msg}")
        if not isinstance(parsed, dict):
            return ("PCT-013", "FAIL", f"line {lineno} is not a JSON object")
        records.append(parsed)

    if not records:
        return ("PCT-013", "FAIL", "mica.observe.jsonl is empty")

    seen_event_ids: set[str] = set()
    previous_hash: str | None = None
    previous_timestamp: str | None = None
    timestamp_regressed = False
    for index, record in enumerate(records, start=1):
        missing = [field for field in _OBSERVE_REQUIRED_FIELDS if field not in record]
        if missing:
            return ("PCT-013", "FAIL", f"record {index} missing required fields: {missing}")
        if record.get("schema_version") != "mica.observe.v1":
            return ("PCT-013", "FAIL", f"record {index} has unsupported schema_version: {record.get('schema_version')}")
        event_id = record.get("event_id")
        if not _is_non_empty_string(event_id):
            return ("PCT-013", "FAIL", f"record {index} has invalid event_id")
        if event_id in seen_event_ids:
            return ("PCT-013", "FAIL", f"duplicate event_id detected: {event_id}")
        seen_event_ids.add(event_id)
        if record.get("event_hash") != compute_observation_event_hash(record):
            return ("PCT-013", "FAIL", f"record {index} event_hash mismatch for {event_id}")
        prev_hash = record.get("prev_event_hash")
        if previous_hash is None:
            if prev_hash not in (None, ""):
                return ("PCT-013", "FAIL", f"record {index} unexpectedly declares prev_event_hash at stream head")
        elif prev_hash != previous_hash:
            return ("PCT-013", "FAIL", f"record {index} prev_event_hash mismatch for {event_id}")
        previous_hash = str(record.get("event_hash"))
        timestamp = record.get("timestamp_utc")
        if _is_non_empty_string(previous_timestamp) and _is_non_empty_string(timestamp) and str(timestamp) < str(previous_timestamp):
            timestamp_regressed = True
        previous_timestamp = str(timestamp)

    if timestamp_regressed:
        return ("PCT-013", "WARN", f"{observe_path.relative_to(project_root)} coherent but timestamps are not monotonic")
    return ("PCT-013", "PASS", f"{observe_path.relative_to(project_root)} parseable and hash-chain coherent ({len(records)} records)")


def _run_pct015(project_root: Path, flow_policy: dict[str, Any]) -> tuple[str, str, str]:
    if not _flow_enabled(flow_policy):
        return ("PCT-015", "INFO", "flow disabled; promotion provenance not required")

    candidates_path = find_flow_artifact(project_root, "mica.candidates.json")
    if not candidates_path:
        return ("PCT-015", "FAIL", "flow enabled but mica.candidates.json missing")
    candidates_doc = load_json(candidates_path)
    if candidates_doc.get("schema_version") != "mica.candidates.v1":
        return ("PCT-015", "FAIL", f"candidate registry has unsupported schema_version: {candidates_doc.get('schema_version')}")
    candidates = candidates_doc.get("candidates")
    if not isinstance(candidates, list):
        return ("PCT-015", "FAIL", "candidate registry missing candidates list")
    observe_path = find_flow_artifact(project_root, "mica.observe.jsonl")
    if not observe_path:
        return ("PCT-015", "FAIL", "cannot validate promotion provenance because mica.observe.jsonl is missing")
    observations = load_jsonl(observe_path)
    observation_ids = {record.get("event_id") for record in observations if _is_non_empty_string(record.get("event_id"))}
    governed = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return ("PCT-015", "FAIL", "candidate registry contains a non-object item")
        if candidate.get("stage") in {"approved_lesson", "bound_invariant_evidence"}:
            governed.append(candidate)
    if not governed:
        return ("PCT-015", "INFO", f"{candidates_path.relative_to(project_root)} contains no approved or promoted artifacts requiring provenance validation")

    issues: list[str] = []
    for candidate in governed:
        candidate_id = str(candidate.get("candidate_id") or "?")
        source_event_ids = candidate.get("source_event_ids")
        if not isinstance(source_event_ids, list) or not source_event_ids:
            issues.append(f"{candidate_id}: missing source_event_ids")
        else:
            missing_source_ids = [source_id for source_id in source_event_ids if source_id not in observation_ids]
            if missing_source_ids:
                issues.append(f"{candidate_id}: unknown source_event_ids {missing_source_ids}")
        if not _review_is_approved(candidate.get("operator_review")):
            issues.append(f"{candidate_id}: operator_review must be approved with non-null review metadata")
        if candidate.get("stage") == "bound_invariant_evidence":
            if not _is_non_empty_string(candidate.get("origin_episode")):
                issues.append(f"{candidate_id}: missing origin_episode")
            supporting_event_ids = candidate.get("supporting_event_ids")
            if not isinstance(supporting_event_ids, list) or not supporting_event_ids:
                issues.append(f"{candidate_id}: missing supporting_event_ids")
            else:
                missing_support_ids = [event_id for event_id in supporting_event_ids if event_id not in observation_ids]
                if missing_support_ids:
                    issues.append(f"{candidate_id}: unknown supporting_event_ids {missing_support_ids}")
            if candidate.get("trust_basis") == "opaque_observation_trace":
                issues.append(f"{candidate_id}: Stage 3 evidence may not use opaque trust_basis")
    if issues:
        preview = "; ".join(issues[:4])
        if len(issues) > 4:
            preview += f"; ... (+{len(issues) - 4} more)"
        return ("PCT-015", "FAIL", preview)
    return ("PCT-015", "PASS", f"validated promotion provenance for {len(governed)} governed candidate(s)")

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
    op_meta = archive.get("operation_meta") if isinstance(archive.get("operation_meta"), dict) else {}
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




def _run_pct014(
    project_root: Path, flow_policy: dict[str, Any], recall_policy: dict[str, Any]
) -> tuple[str, str, str]:
    if not _flow_enabled(flow_policy):
        return ("PCT-014", "INFO", "flow disabled; recall trace coverage not required")

    recall_enabled = bool(recall_policy.get("enabled", False))
    recall_path = find_flow_artifact(project_root, "mica.recall.jsonl")
    if not recall_enabled and not recall_path:
        return ("PCT-014", "INFO", "recall trace inactive")
    if not recall_path:
        return ("PCT-014", "WARN", "recall enabled but mica.recall.jsonl missing")

    try:
        records = load_jsonl(recall_path)
    except Exception as exc:
        return ("PCT-014", "WARN", f"cannot parse recall trace: {exc}")
    if not records:
        return ("PCT-014", "WARN", f"{recall_path.relative_to(project_root)} empty while recall is active")

    issues: list[str] = []
    for index, record in enumerate(records, start=1):
        if record.get("schema_version") != "mica.recall.v1":
            issues.append(f"record {index}: unsupported schema_version {record.get('schema_version')}")
        target = record.get("target")
        if target not in {"operator_review", "agent_context"}:
            issues.append(f"record {index}: invalid target {target!r}")
        if not _is_non_empty_string(record.get("candidate_id")):
            issues.append(f"record {index}: missing candidate_id")
        if not _is_non_empty_string(record.get("recall_id")):
            issues.append(f"record {index}: missing recall_id")
        if not _is_non_empty_string(record.get("session_id")):
            issues.append(f"record {index}: missing session_id")

    if issues:
        preview = "; ".join(issues[:4])
        if len(issues) > 4:
            preview += f"; ... (+{len(issues) - 4} more)"
        return ("PCT-014", "WARN", preview)
    return ("PCT-014", "PASS", f"{recall_path.relative_to(project_root)} provides recall trace coverage ({len(records)} records)")


def _run_pct018(
    project_root: Path, flow_policy: dict[str, Any]
) -> tuple[str, str, str]:
    if not _flow_enabled(flow_policy):
        return ("PCT-018", "INFO", "flow disabled; telemetry completeness not required")

    recall_path = find_flow_artifact(project_root, "mica.recall.jsonl")
    if not recall_path:
        return ("PCT-018", "INFO", "recall trace absent; telemetry completeness not active")

    observe_path = find_flow_artifact(project_root, "mica.observe.jsonl")
    candidates_path = find_flow_artifact(project_root, "mica.candidates.json")
    try:
        observations = load_jsonl(observe_path)
    except Exception as exc:
        return ("PCT-018", "WARN", f"cannot load observation stream for telemetry completeness: {exc}")
    candidates_doc = load_json(candidates_path)
    candidates = candidates_doc.get("candidates") if isinstance(candidates_doc.get("candidates"), list) else []
    try:
        recall_records = load_jsonl(recall_path)
    except Exception as exc:
        return ("PCT-018", "WARN", f"cannot load recall trace for telemetry completeness: {exc}")
    if not recall_records:
        return ("PCT-018", "INFO", "recall trace empty; completeness deferred to PCT-014 coverage warning")

    observation_ids = {
        record.get("event_id")
        for record in observations
        if _is_non_empty_string(record.get("event_id"))
    }
    observation_sessions = {
        record.get("session_id")
        for record in observations
        if _is_non_empty_string(record.get("session_id"))
    }
    candidate_map = {
        candidate.get("candidate_id"): candidate
        for candidate in candidates
        if isinstance(candidate, dict) and _is_non_empty_string(candidate.get("candidate_id"))
    }

    issues: list[str] = []
    for index, record in enumerate(recall_records, start=1):
        candidate_id = record.get("candidate_id")
        if not _is_non_empty_string(candidate_id):
            issues.append(f"record {index}: missing candidate_id")
            continue
        candidate = candidate_map.get(candidate_id)
        if not isinstance(candidate, dict):
            issues.append(f"record {index}: candidate_id {candidate_id} not found in mica.candidates.json")
            continue

        session_id = record.get("session_id")
        if not _is_non_empty_string(session_id) or session_id not in observation_sessions:
            issues.append(f"record {index}: session_id {session_id!r} not linked to observation stream")

        source_event_ids = record.get("source_event_ids")
        if not isinstance(source_event_ids, list) or not source_event_ids:
            issues.append(f"record {index}: missing source_event_ids for candidate {candidate_id}")
            continue

        missing_observation_ids = [event_id for event_id in source_event_ids if event_id not in observation_ids]
        if missing_observation_ids:
            issues.append(f"record {index}: source_event_ids not found in observation stream: {missing_observation_ids}")

        candidate_source_ids = candidate.get("source_event_ids")
        if isinstance(candidate_source_ids, list):
            extra_ids = [event_id for event_id in source_event_ids if event_id not in candidate_source_ids]
            if extra_ids:
                issues.append(f"record {index}: source_event_ids not declared on candidate {candidate_id}: {extra_ids}")

    if issues:
        preview = "; ".join(issues[:4])
        if len(issues) > 4:
            preview += f"; ... (+{len(issues) - 4} more)"
        return ("PCT-018", "WARN", preview)
    return ("PCT-018", "PASS", f"{recall_path.relative_to(project_root)} joins cleanly with candidates and observations")

def _run_pct017(
    project_root: Path, flow_policy: dict[str, Any], recall_policy: dict[str, Any]
) -> tuple[str, str, str]:
    if not _flow_enabled(flow_policy):
        return ("PCT-017", "INFO", "flow disabled; recall injection safety not required")

    recall_enabled = bool(recall_policy.get("enabled", False))
    recall_path = find_flow_artifact(project_root, "mica.recall.jsonl")
    if not recall_enabled and not recall_path:
        return ("PCT-017", "INFO", "recall trace absent; runtime injection safety not active")
    if not recall_path:
        return ("PCT-017", "INFO", "recall enabled but trace file absent; PCT-017 deferred until runtime trace exists")

    candidates_path = find_flow_artifact(project_root, "mica.candidates.json")
    candidates_doc = load_json(candidates_path)
    candidates = candidates_doc.get("candidates") if isinstance(candidates_doc.get("candidates"), list) else []
    candidate_map = {
        candidate.get("candidate_id"): candidate
        for candidate in candidates
        if isinstance(candidate, dict) and _is_non_empty_string(candidate.get("candidate_id"))
    }

    try:
        records = load_jsonl(recall_path)
    except Exception as exc:
        return ("PCT-017", "FAIL", f"cannot parse recall trace: {exc}")
    if not records:
        return ("PCT-017", "INFO", f"{recall_path.relative_to(project_root)} empty; no recall injection recorded")

    inject_unapproved = bool(recall_policy.get("inject_unapproved_candidates", False))
    issues: list[str] = []
    for index, record in enumerate(records, start=1):
        if record.get("schema_version") != "mica.recall.v1":
            issues.append(f"record {index}: unsupported schema_version {record.get('schema_version')}")
            continue
        target = record.get("target")
        if target not in {"operator_review", "agent_context"}:
            issues.append(f"record {index}: invalid target {target!r}")
            continue
        candidate_id = record.get("candidate_id")
        if not _is_non_empty_string(candidate_id):
            issues.append(f"record {index}: missing candidate_id")
            continue
        candidate = candidate_map.get(candidate_id)
        if not isinstance(candidate, dict):
            issues.append(f"record {index}: unknown candidate_id {candidate_id}")
            continue
        status = candidate.get("status")
        if target != "agent_context":
            continue
        if status in {"rejected", "superseded"}:
            issues.append(f"candidate {candidate_id} entered agent_context while status={status}")
            continue
        if not inject_unapproved and status not in {"approved", "promoted"}:
            review = candidate.get("operator_review") if isinstance(candidate.get("operator_review"), dict) else {}
            review_state = review.get("state") or "unknown"
            issues.append(
                f"candidate {candidate_id} entered agent_context while operator_review.state={review_state}"
            )

    if issues:
        preview = "; ".join(issues[:4])
        if len(issues) > 4:
            preview += f"; ... (+{len(issues) - 4} more)"
        return ("PCT-017", "FAIL", preview)
    return ("PCT-017", "PASS", f"{recall_path.relative_to(project_root)} enforces approved-only agent_context injection")

# ---------------------------------------------------------------------------
# PCT checks
# ---------------------------------------------------------------------------


def run_pct_checks(project_root: Path) -> list[tuple[str, str, str]]:
    """
    Run PCT-001 through PCT-018. Returns list of (id, status, message).
    Hard-fail checks: PCT-001, 002, 003, 004, 007, 008, 010, 013, 015, 017.
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
    elif mode == "memory_first" and {
        "archive",
        "playbook",
        "sessions",
        "observations",
        "memories",
        "slots",
    } <= layer_role_set:
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
    contract = resolve_invocation_contract(yd)
    invoked_surfaces = contract["loaded_surfaces"]
    context_surfaces = contract["agent_context_surfaces"]
    missing_invoked_surfaces = contract["missing_invoked_surfaces"]
    invoked_label = ", ".join(invoked_surfaces) if invoked_surfaces else "none"
    context_label = ", ".join(context_surfaces) if context_surfaces else "none"
    valid_patterns = {
        "readme_protocol",
        "hook_trigger",
        "agent_yaml_bootstrap",
        "global_skill",
        "workspace_directive",
        "explicit",
    }
    if pattern is None:
        if missing_invoked_surfaces:
            results.append(
                (
                    "PCT-007",
                    "FAIL",
                    f"invocation contract incomplete; missing required session-start surfaces {missing_invoked_surfaces} (invoked={invoked_label}; context={context_label})",
                )
            )
        else:
            results.append(
                (
                    "PCT-007",
                    "INFO",
                    f"invocation_protocol absent (default/manual handling); invoked={invoked_label}; context={context_label}",
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
    else:
        results.append(("PCT-007", "PASS", f"primary_pattern valid: {pattern}; invoked={invoked_label}; context={context_label}"))

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

    results.append(_run_pct013(project_root, flow_policy))
    results.append(_run_pct014(project_root, flow_policy, recall_policy))
    results.append(_run_pct015(project_root, flow_policy))
    results.append(_run_pct018(project_root, flow_policy))
    results.append(_run_pct017(project_root, flow_policy, recall_policy))

    fails = [r[0] for r in results if r[1] == "FAIL" and r[0] in HARD_FAIL_CHECKS]
    if fails:
        results.append(("PCT-009", "FAIL", f"package incomplete. failing checks: {fails}"))
    else:
        results.append(("PCT-009", "PASS", "package complete. closed contract verified."))

    return results


def is_closed_contract(results: list[tuple[str, str, str]]) -> bool:
    return not any(r[1] == "FAIL" and r[0] in HARD_FAIL_CHECKS for r in results)


