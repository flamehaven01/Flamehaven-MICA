#!/usr/bin/env python3
"""
MICA memory-first utility v0.2.8.

Provides minimal read/write helpers for memory-first packages:

- resolve kind-based layer paths from mica.yaml
- append and read observation records
- append session, memory, and graph records
- read session, memory, graph, and slot artifacts
- upsert slot projections
- synthesize candidate memories from observations
- review and promote candidate memories
- synthesize slots and graph projections from memories
- export governed archive/playbook surfaces from memories
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from mica_core import MICA_TOOL_VERSION, find_mica_yaml, load_yaml

__version__ = MICA_TOOL_VERSION

_SESSIONS_REQUIRED_FIELDS = (
    "schema_version",
    "session_id",
    "opened_at_utc",
    "closed_at_utc",
    "project_scope",
    "actors",
    "source",
    "session_hash",
)

_OBSERVATIONS_REQUIRED_FIELDS = (
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

_MEMORIES_REQUIRED_FIELDS = (
    "schema_version",
    "memory_id",
    "created_at_utc",
    "updated_at_utc",
    "kind",
    "status",
    "project_scope",
    "summary",
    "source_event_ids",
    "source_session_ids",
    "trust_basis",
    "promotion_stage",
    "slot_refs",
    "graph_refs",
)

_GRAPH_REQUIRED_FIELDS = (
    "schema_version",
    "edge_id",
    "from_ref",
    "to_ref",
    "relation",
    "created_at_utc",
    "source_event_ids",
)

_SLOTS_REQUIRED_FIELDS = ("schema_version", "slots")
_SLOT_REQUIRED_FIELDS = ("slot_id", "value_ref", "updated_at_utc", "stability")
_EXPORTABLE_STATUSES = {"approved", "promoted"}
_ARCHIVE_EXPORT_STAGES = {
    "approved_lesson",
    "bound_invariant_evidence",
    "exported_archive",
    "exported_playbook",
}
_PLAYBOOK_EXPORT_STAGES = {"approved_lesson", "exported_playbook"}
_REVIEW_DECISIONS = {
    "approved_lesson",
    "bound_invariant_evidence",
    "rejected",
    "superseded",
}
_ACTIVE_MEMORY_STATUSES = {"active", "approved", "promoted"}
_HOOK_TO_MEMORY_KIND = {
    "session_start": "task_state",
    "session_end": "task_state",
    "file_edit": "task_state",
    "operator_decision": "decision",
    "post_tool_failure": "constraint",
}
_TRUST_TIER_TO_BASIS = {
    "native": "native_observation_trace",
    "attested": "attested_observation_trace",
    "opaque": "opaque_observation_trace",
}


@dataclass(frozen=True)
class MemoryFirstPaths:
    project_root: Path
    mica_yaml: Path
    archive: Path
    playbook: Path
    sessions: Path
    observations: Path
    memories: Path
    recall: Path | None
    slots: Path
    graph: Path | None


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _layer_role(layer: dict[str, Any]) -> str:
    for field in ("kind", "name"):
        value = layer.get(field)
        if _is_non_empty_string(value):
            return str(value)
    return ""


def _require_fields(record: dict[str, Any], required_fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in required_fields if field not in record]
    if missing:
        raise ValueError(f"{label} missing required fields: {missing}")


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    result: list[dict[str, Any]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            record = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path} line {lineno} JSON parse error: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{path} line {lineno} must be a JSON object")
        result.append(record)
    return result


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(serialized)
        fh.write("\n")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            serialized = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            fh.write(serialized)
            fh.write("\n")


def resolve_memory_first_paths(project_root: Path) -> MemoryFirstPaths:
    mica_yaml = find_mica_yaml(project_root)
    if not mica_yaml:
        raise FileNotFoundError(f"mica.yaml not found under {project_root}")

    yd = load_yaml(mica_yaml)
    if yd.get("mode") != "memory_first":
        raise ValueError(f"{mica_yaml} does not declare mode=memory_first")

    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
    layer_paths: dict[str, Path] = {}
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        role = _layer_role(layer)
        rel = layer.get("path")
        if not role or not isinstance(rel, str):
            continue
        layer_paths[role] = project_root / rel

    required_roles = ("archive", "playbook", "sessions", "observations", "memories", "slots")
    missing_roles = [role for role in required_roles if role not in layer_paths]
    if missing_roles:
        raise ValueError(f"memory_first package missing required layer roles: {missing_roles}")

    return MemoryFirstPaths(
        project_root=project_root,
        mica_yaml=mica_yaml,
        archive=layer_paths["archive"],
        playbook=layer_paths["playbook"],
        sessions=layer_paths["sessions"],
        observations=layer_paths["observations"],
        memories=layer_paths["memories"],
        recall=layer_paths.get("recall"),
        slots=layer_paths["slots"],
        graph=layer_paths.get("graph"),
    )


def load_sessions(project_root: Path) -> list[dict[str, Any]]:
    return _load_jsonl(resolve_memory_first_paths(project_root).sessions)


def append_session(project_root: Path, record: dict[str, Any]) -> None:
    _require_fields(record, _SESSIONS_REQUIRED_FIELDS, "session record")
    if record.get("schema_version") != "mica.sessions.v1":
        raise ValueError("session record must declare schema_version=mica.sessions.v1")
    _append_jsonl(resolve_memory_first_paths(project_root).sessions, record)


def load_observations(project_root: Path) -> list[dict[str, Any]]:
    return _load_jsonl(resolve_memory_first_paths(project_root).observations)


def append_observation(project_root: Path, record: dict[str, Any]) -> None:
    _require_fields(record, _OBSERVATIONS_REQUIRED_FIELDS, "observation record")
    if record.get("schema_version") != "mica.observe.v1":
        raise ValueError("observation record must declare schema_version=mica.observe.v1")
    _append_jsonl(resolve_memory_first_paths(project_root).observations, record)


def load_memories(project_root: Path) -> list[dict[str, Any]]:
    return _load_jsonl(resolve_memory_first_paths(project_root).memories)


def append_memory(project_root: Path, record: dict[str, Any]) -> None:
    _require_fields(record, _MEMORIES_REQUIRED_FIELDS, "memory record")
    if record.get("schema_version") != "mica.memories.v1":
        raise ValueError("memory record must declare schema_version=mica.memories.v1")
    _append_jsonl(resolve_memory_first_paths(project_root).memories, record)


def write_memories(project_root: Path, records: list[dict[str, Any]]) -> None:
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("memory stream may contain only JSON objects")
        _require_fields(record, _MEMORIES_REQUIRED_FIELDS, "memory record")
        if record.get("schema_version") != "mica.memories.v1":
            raise ValueError("memory record must declare schema_version=mica.memories.v1")
    _write_jsonl(resolve_memory_first_paths(project_root).memories, records)


def load_graph(project_root: Path) -> list[dict[str, Any]]:
    paths = resolve_memory_first_paths(project_root)
    if not paths.graph:
        return []
    return _load_jsonl(paths.graph)


def append_graph(project_root: Path, record: dict[str, Any]) -> None:
    _require_fields(record, _GRAPH_REQUIRED_FIELDS, "graph record")
    if record.get("schema_version") != "mica.graph.v1":
        raise ValueError("graph record must declare schema_version=mica.graph.v1")
    paths = resolve_memory_first_paths(project_root)
    if not paths.graph:
        raise ValueError("memory_first package does not declare a graph layer")
    _append_jsonl(paths.graph, record)


def write_graph(project_root: Path, records: list[dict[str, Any]]) -> None:
    paths = resolve_memory_first_paths(project_root)
    if not paths.graph:
        raise ValueError("memory_first package does not declare a graph layer")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("graph stream may contain only JSON objects")
        _require_fields(record, _GRAPH_REQUIRED_FIELDS, "graph record")
        if record.get("schema_version") != "mica.graph.v1":
            raise ValueError("graph record must declare schema_version=mica.graph.v1")
    _write_jsonl(paths.graph, records)


def load_slots(project_root: Path) -> dict[str, Any]:
    path = resolve_memory_first_paths(project_root).slots
    if not path.exists():
        return {"schema_version": "mica.slots.v1", "slots": []}
    data = _load_json_file(path)
    _require_fields(data, _SLOTS_REQUIRED_FIELDS, "slots document")
    if data.get("schema_version") != "mica.slots.v1":
        raise ValueError("slots document must declare schema_version=mica.slots.v1")
    slots = data.get("slots")
    if not isinstance(slots, list):
        raise ValueError("slots document must contain a slots list")
    return data


def write_slots(project_root: Path, document: dict[str, Any]) -> None:
    _require_fields(document, _SLOTS_REQUIRED_FIELDS, "slots document")
    if document.get("schema_version") != "mica.slots.v1":
        raise ValueError("slots document must declare schema_version=mica.slots.v1")
    slots = document.get("slots")
    if not isinstance(slots, list):
        raise ValueError("slots document must contain a slots list")
    for slot in slots:
        if not isinstance(slot, dict):
            raise ValueError("each slot must be a JSON object")
        _require_fields(slot, _SLOT_REQUIRED_FIELDS, "slot record")
    path = resolve_memory_first_paths(project_root).slots
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def upsert_slot(project_root: Path, slot: dict[str, Any]) -> None:
    _require_fields(slot, _SLOT_REQUIRED_FIELDS, "slot record")
    document = load_slots(project_root)
    slots = document.get("slots", [])
    assert isinstance(slots, list)
    slot_id = slot["slot_id"]
    for index, existing in enumerate(slots):
        if isinstance(existing, dict) and existing.get("slot_id") == slot_id:
            slots[index] = slot
            break
    else:
        slots.append(slot)
    document["slots"] = slots
    write_slots(project_root, document)


def _sanitize_memory_ref(value: str) -> str:
    sanitized = []
    for ch in value.lower():
        if ch.isalnum() or ch in "._:-":
            sanitized.append(ch)
        else:
            sanitized.append("-")
    result = "".join(sanitized).strip("-")
    return result or "unknown"


def _edge_id(*parts: str) -> str:
    joined = ".".join(_sanitize_memory_ref(part) for part in parts if _is_non_empty_string(part))
    return f"edge.{joined}" if joined else "edge.unknown"


def _pick_latest(memories: list[dict[str, Any]], predicate: Any) -> dict[str, Any] | None:
    candidates = [memory for memory in memories if isinstance(memory, dict) and predicate(memory)]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda memory: (
            str(memory.get("updated_at_utc") or memory.get("created_at_utc") or ""),
            str(memory.get("memory_id") or ""),
        ),
    )


def _infer_memory_kind(observation: dict[str, Any]) -> str:
    hook = str(observation.get("hook") or "")
    return _HOOK_TO_MEMORY_KIND.get(hook, "fact")


def _infer_trust_basis(observation: dict[str, Any]) -> str:
    trust_tier = str(observation.get("trust_tier") or "")
    return _TRUST_TIER_TO_BASIS.get(trust_tier, "mixed_observation_trace")


def _find_memory_index(memories: list[dict[str, Any]], memory_id: str) -> int:
    for index, memory in enumerate(memories):
        if isinstance(memory, dict) and memory.get("memory_id") == memory_id:
            return index
    raise ValueError(f"memory_id not found: {memory_id}")


def _build_operator_review(review: dict[str, Any], state: str) -> dict[str, Any]:
    reviewed_by = review.get("reviewed_by")
    reviewed_at_utc = review.get("reviewed_at_utc")
    decision_reason = review.get("decision_reason")
    if not _is_non_empty_string(reviewed_by):
        raise ValueError("review requires non-empty reviewed_by")
    if not _is_non_empty_string(reviewed_at_utc):
        raise ValueError("review requires non-empty reviewed_at_utc")
    if not _is_non_empty_string(decision_reason):
        raise ValueError("review requires non-empty decision_reason")
    return {
        "state": state,
        "reviewed_by": str(reviewed_by),
        "reviewed_at_utc": str(reviewed_at_utc),
        "decision_reason": str(decision_reason),
    }


def _default_di_id(index: int) -> str:
    return f"DI-MEM-{index:03d}"


def _default_di_label(memory: dict[str, Any]) -> str:
    summary = str(memory.get("summary") or "")
    base = _sanitize_memory_ref(summary.replace(" ", "-"))[:48]
    return base or _sanitize_memory_ref(str(memory.get("memory_id") or "memory-export"))


def _bound_memories(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for memory in memories:
        if not isinstance(memory, dict):
            continue
        if memory.get("status") not in _EXPORTABLE_STATUSES:
            continue
        if memory.get("promotion_stage") == "bound_invariant_evidence":
            selected.append(memory)
    return _sort_memories(selected)


def synthesize_memories(project_root: Path) -> list[dict[str, Any]]:
    observations = load_observations(project_root)
    existing_memories = load_memories(project_root)
    covered_event_ids = {
        event_id
        for memory in existing_memories
        if isinstance(memory, dict)
        for event_id in memory.get("source_event_ids", [])
        if _is_non_empty_string(event_id)
    }
    existing_memory_ids = {
        str(memory.get("memory_id"))
        for memory in existing_memories
        if isinstance(memory, dict) and _is_non_empty_string(memory.get("memory_id"))
    }

    created: list[dict[str, Any]] = []
    for observation in observations:
        if not isinstance(observation, dict):
            continue
        event_id = observation.get("event_id")
        if not _is_non_empty_string(event_id) or event_id in covered_event_ids:
            continue
        session_id = observation.get("session_id")
        timestamp_utc = str(observation.get("timestamp_utc") or "")
        scope = observation.get("scope") if isinstance(observation.get("scope"), dict) else {}
        project_scope = scope.get("project") if _is_non_empty_string(scope.get("project")) else project_root.name
        memory_id = f"mem.obs.{_sanitize_memory_ref(str(event_id))}"
        if memory_id in existing_memory_ids:
            continue
        memory = {
            "schema_version": "mica.memories.v1",
            "memory_id": memory_id,
            "created_at_utc": timestamp_utc,
            "updated_at_utc": timestamp_utc,
            "kind": _infer_memory_kind(observation),
            "status": "active",
            "project_scope": project_scope,
            "summary": str(observation.get("summary") or "").strip(),
            "source_event_ids": [event_id],
            "source_session_ids": [session_id] if _is_non_empty_string(session_id) else [],
            "trust_basis": _infer_trust_basis(observation),
            "promotion_stage": "candidate_memory",
            "slot_refs": [],
            "graph_refs": [],
        }
        append_memory(project_root, memory)
        created.append(memory)
        covered_event_ids.add(event_id)
        existing_memory_ids.add(memory_id)
    return created


def synthesize_slots(project_root: Path) -> dict[str, Any]:
    memories = load_memories(project_root)
    slots: list[dict[str, Any]] = []

    active_goal = _pick_latest(
        memories,
        lambda memory: memory.get("kind") == "task_state" and memory.get("status") in _ACTIVE_MEMORY_STATUSES,
    )
    if active_goal:
        slots.append(
            {
                "slot_id": "active_goal",
                "slot_kind": "active_goal",
                "value_ref": active_goal["memory_id"],
                "updated_at_utc": active_goal["updated_at_utc"],
                "stability": "volatile",
                "source_memory_ids": [active_goal["memory_id"]],
            }
        )

    next_operator_decision = _pick_latest(
        memories,
        lambda memory: memory.get("promotion_stage") == "candidate_memory"
        and memory.get("status") in {"active", "pending_review"},
    )
    if next_operator_decision:
        slots.append(
            {
                "slot_id": "next_operator_decision",
                "slot_kind": "next_operator_decision",
                "value_ref": next_operator_decision["memory_id"],
                "updated_at_utc": next_operator_decision["updated_at_utc"],
                "stability": "volatile",
                "source_memory_ids": [next_operator_decision["memory_id"]],
            }
        )

    current_invariant_set = _pick_latest(
        memories,
        lambda memory: memory.get("promotion_stage") == "bound_invariant_evidence"
        and memory.get("status") in _ACTIVE_MEMORY_STATUSES,
    )
    if current_invariant_set:
        slots.append(
            {
                "slot_id": "current_invariant_set",
                "slot_kind": "current_invariant_set",
                "value_ref": current_invariant_set["memory_id"],
                "updated_at_utc": current_invariant_set["updated_at_utc"],
                "stability": "pinned",
                "source_memory_ids": [current_invariant_set["memory_id"]],
            }
        )

    document = {"schema_version": "mica.slots.v1", "slots": slots}
    write_slots(project_root, document)
    return document


def synthesize_graph(project_root: Path) -> list[dict[str, Any]]:
    memories = _sort_memories(load_memories(project_root))
    edges: list[dict[str, Any]] = []
    seen_edge_ids: set[str] = set()

    for memory in memories:
        memory_id = str(memory.get("memory_id") or "")
        created_at = str(memory.get("updated_at_utc") or memory.get("created_at_utc") or "")
        source_event_ids = memory.get("source_event_ids", [])
        if not memory_id or not isinstance(source_event_ids, list):
            continue

        for session_id in memory.get("source_session_ids", []):
            if not _is_non_empty_string(session_id):
                continue
            edge = {
                "schema_version": "mica.graph.v1",
                "edge_id": _edge_id(memory_id, "belongs_to_session", str(session_id)),
                "from_ref": memory_id,
                "to_ref": str(session_id),
                "relation": "belongs_to_session",
                "created_at_utc": created_at,
                "source_event_ids": source_event_ids,
            }
            if edge["edge_id"] not in seen_edge_ids:
                edges.append(edge)
                seen_edge_ids.add(edge["edge_id"])

        for event_id in memory.get("supporting_event_ids", []):
            if not _is_non_empty_string(event_id):
                continue
            edge = {
                "schema_version": "mica.graph.v1",
                "edge_id": _edge_id(memory_id, "supports", str(event_id)),
                "from_ref": memory_id,
                "to_ref": str(event_id),
                "relation": "supports",
                "created_at_utc": created_at,
                "source_event_ids": source_event_ids,
            }
            if edge["edge_id"] not in seen_edge_ids:
                edges.append(edge)
                seen_edge_ids.add(edge["edge_id"])

        if memory.get("promotion_stage") in _ARCHIVE_EXPORT_STAGES:
            edge = {
                "schema_version": "mica.graph.v1",
                "edge_id": _edge_id(memory_id, "exported_as", "archive_export"),
                "from_ref": memory_id,
                "to_ref": "archive_export",
                "relation": "exported_as",
                "created_at_utc": created_at,
                "source_event_ids": source_event_ids,
            }
            if edge["edge_id"] not in seen_edge_ids:
                edges.append(edge)
                seen_edge_ids.add(edge["edge_id"])

        if memory.get("promotion_stage") in _PLAYBOOK_EXPORT_STAGES or memory.get("kind") == "lesson":
            edge = {
                "schema_version": "mica.graph.v1",
                "edge_id": _edge_id(memory_id, "exported_as", "playbook_export"),
                "from_ref": memory_id,
                "to_ref": "playbook_export",
                "relation": "exported_as",
                "created_at_utc": created_at,
                "source_event_ids": source_event_ids,
            }
            if edge["edge_id"] not in seen_edge_ids:
                edges.append(edge)
                seen_edge_ids.add(edge["edge_id"])

    write_graph(project_root, edges)
    return edges


def refresh_projections(project_root: Path) -> dict[str, Any]:
    slots = synthesize_slots(project_root)
    edges = synthesize_graph(project_root)
    return {"slot_count": len(slots["slots"]), "edge_count": len(edges)}


def review_memory(project_root: Path, memory_id: str, review: dict[str, Any]) -> dict[str, Any]:
    decision = review.get("decision")
    if decision not in _REVIEW_DECISIONS:
        raise ValueError(f"decision must be one of {sorted(_REVIEW_DECISIONS)}")

    memories = load_memories(project_root)
    index = _find_memory_index(memories, memory_id)
    current = dict(memories[index])
    updated = dict(current)

    reviewed_at_utc = str(review.get("reviewed_at_utc") or current.get("updated_at_utc") or "")
    updated["updated_at_utc"] = reviewed_at_utc

    if decision == "approved_lesson":
        updated["kind"] = "lesson"
        updated["status"] = "approved"
        updated["promotion_stage"] = "approved_lesson"
        updated["operator_review"] = _build_operator_review(review, "approved")
    elif decision == "bound_invariant_evidence":
        if updated.get("trust_basis") == "opaque_observation_trace":
            raise ValueError("opaque_observation_trace may not be promoted to bound_invariant_evidence")
        origin_episode = review.get("origin_episode")
        supporting_event_ids = review.get("supporting_event_ids")
        if not _is_non_empty_string(origin_episode):
            raise ValueError("bound_invariant_evidence promotion requires origin_episode")
        if not isinstance(supporting_event_ids, list) or not supporting_event_ids:
            raise ValueError("bound_invariant_evidence promotion requires supporting_event_ids")
        updated["status"] = "promoted"
        updated["promotion_stage"] = "bound_invariant_evidence"
        updated["origin_episode"] = str(origin_episode)
        updated["supporting_event_ids"] = supporting_event_ids
        if _is_non_empty_string(review.get("di_id")):
            updated["di_id"] = str(review.get("di_id"))
        if _is_non_empty_string(review.get("di_label")):
            updated["di_label"] = str(review.get("di_label"))
        if _is_non_empty_string(review.get("di_statement")):
            updated["di_statement"] = str(review.get("di_statement"))
        if _is_non_empty_string(review.get("severity")):
            updated["severity"] = str(review.get("severity"))
        updated["operator_review"] = _build_operator_review(review, "approved")
    elif decision == "rejected":
        updated["status"] = "rejected"
        updated["operator_review"] = _build_operator_review(review, "rejected")
    elif decision == "superseded":
        updated["status"] = "superseded"
        updated["operator_review"] = _build_operator_review(review, "superseded")

    memories[index] = updated
    write_memories(project_root, memories)
    return updated


def _sort_memories(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        memories,
        key=lambda item: (
            str(item.get("updated_at_utc") or item.get("created_at_utc") or ""),
            str(item.get("memory_id") or ""),
        ),
    )


def _exportable_memories(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for memory in memories:
        if not isinstance(memory, dict):
            continue
        if memory.get("status") not in _EXPORTABLE_STATUSES:
            continue
        if memory.get("promotion_stage") not in _ARCHIVE_EXPORT_STAGES:
            continue
        selected.append(memory)
    return _sort_memories(selected)


def _playbook_memories(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for memory in memories:
        if not isinstance(memory, dict):
            continue
        if memory.get("status") not in _EXPORTABLE_STATUSES:
            continue
        if memory.get("promotion_stage") in _PLAYBOOK_EXPORT_STAGES or memory.get("kind") == "lesson":
            selected.append(memory)
    return _sort_memories(selected)


def _last_updated_from_memories(memories: list[dict[str, Any]]) -> str:
    stamps = [
        str(memory.get("updated_at_utc"))
        for memory in memories
        if _is_non_empty_string(memory.get("updated_at_utc"))
    ]
    if not stamps:
        return date.today().isoformat()
    return max(stamps)[:10]


def _build_generated_design_invariants(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    generated = []
    for index, memory in enumerate(_bound_memories(memories), start=1):
        source_event_ids = memory.get("source_event_ids", [])
        source_memory_id = str(memory.get("memory_id") or "")
        updated_at_utc = str(memory.get("updated_at_utc") or "")
        invariant = {
            "id": memory.get("di_id") or _default_di_id(index),
            "label": memory.get("di_label") or _default_di_label(memory),
            "statement": memory.get("di_statement") or str(memory.get("summary") or "").strip(),
            "severity": memory.get("severity") or "high",
            "binding": {
                "origin_episode": memory.get("origin_episode"),
                "last_triggered": updated_at_utc[:10] if updated_at_utc else None,
                "violation_count": 0,
            },
            "track": "memory_first_export",
            "source_memory_id": source_memory_id,
            "source_event_ids": source_event_ids,
        }
        generated.append(invariant)
    return generated


def build_archive_export(project_root: Path) -> dict[str, Any]:
    paths = resolve_memory_first_paths(project_root)
    existing = _load_json_file(paths.archive) if paths.archive.exists() else {}
    memories = _exportable_memories(load_memories(project_root))
    exports = []
    for memory in memories:
        exports.append(
            {
                "memory_id": memory.get("memory_id"),
                "kind": memory.get("kind"),
                "summary": memory.get("summary"),
                "promotion_stage": memory.get("promotion_stage"),
                "trust_basis": memory.get("trust_basis"),
                "source_event_ids": memory.get("source_event_ids", []),
                "source_session_ids": memory.get("source_session_ids", []),
                "project_scope": memory.get("project_scope"),
            }
        )

    archive = dict(existing) if isinstance(existing, dict) else {}
    archive["mica_spec"] = "0.2.9"
    project_meta = archive.get("project") if isinstance(archive.get("project"), dict) else {}
    if not isinstance(project_meta, dict):
        project_meta = {}
    if not _is_non_empty_string(project_meta.get("name")):
        project_meta["name"] = project_root.name
    if not _is_non_empty_string(project_meta.get("version")):
        project_meta["version"] = "1.0.0"
    archive["project"] = project_meta
    operation_meta = archive.get("operation_meta") if isinstance(archive.get("operation_meta"), dict) else {}
    operation_meta["last_updated"] = _last_updated_from_memories(memories)
    archive["operation_meta"] = operation_meta
    existing_design_invariants = (
        archive.get("design_invariants") if isinstance(archive.get("design_invariants"), list) else []
    )
    manual_design_invariants = [
        item
        for item in existing_design_invariants
        if not (isinstance(item, dict) and _is_non_empty_string(item.get("source_memory_id")))
    ]
    archive["design_invariants"] = manual_design_invariants + _build_generated_design_invariants(memories)
    archive["memory_exports"] = exports
    return archive


def build_playbook_export(project_root: Path) -> str:
    memories = load_memories(project_root)
    lessons = _playbook_memories(memories)
    approved = _exportable_memories(memories)
    title = f"# {project_root.name} Memory Playbook"
    intro = (
        "This playbook is derived from approved/promoted memories in the memory-first MICA package."
    )
    lines = [title, "", intro, ""]

    lines.append("## Approved Lessons")
    if lessons:
        for memory in lessons:
            memory_id = memory.get("memory_id")
            summary = str(memory.get("summary") or "").strip()
            source_events = ", ".join(memory.get("source_event_ids", []))
            lines.append(f"- `{memory_id}`: {summary}")
            if source_events:
                lines.append(f"  Source events: `{source_events}`")
    else:
        lines.append("- No approved lessons exported yet.")
    lines.append("")

    lines.append("## Governed Memory Exports")
    if approved:
        for memory in approved:
            memory_id = memory.get("memory_id")
            stage = memory.get("promotion_stage")
            summary = str(memory.get("summary") or "").strip()
            lines.append(f"- `{memory_id}` [{stage}]: {summary}")
    else:
        lines.append("- No governed memory exports yet.")
    lines.append("")

    return "\n".join(lines)


def export_surfaces(project_root: Path) -> tuple[Path, Path]:
    paths = resolve_memory_first_paths(project_root)
    archive = build_archive_export(project_root)
    paths.archive.parent.mkdir(parents=True, exist_ok=True)
    paths.archive.write_text(json.dumps(archive, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    playbook_text = build_playbook_export(project_root)
    paths.playbook.parent.mkdir(parents=True, exist_ok=True)
    paths.playbook.write_text(playbook_text + "\n", encoding="utf-8")
    return paths.archive, paths.playbook


def materialize_package(project_root: Path) -> dict[str, Any]:
    created = synthesize_memories(project_root)
    archive_path, playbook_path = export_surfaces(project_root)
    projections = refresh_projections(project_root)
    return {
        "created_memory_count": len(created),
        "created_memory_ids": [item["memory_id"] for item in created],
        "archive": str(archive_path),
        "playbook": str(playbook_path),
        "slot_count": projections["slot_count"],
        "edge_count": projections["edge_count"],
    }


def _load_record_arg(record_file: str) -> dict[str, Any]:
    return _load_json_file(Path(record_file))


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MICA memory-first utility")
    parser.add_argument("project_root", nargs="?", default=".", help="target project root")
    parser.add_argument(
        "command",
        choices=(
            "paths",
            "dump",
            "append-observation",
            "append-session",
            "append-memory",
            "append-graph",
            "write-slots",
            "upsert-slot",
            "synthesize-memories",
            "synthesize-slots",
            "synthesize-graph",
            "refresh-projections",
            "review-memory",
            "export",
            "materialize",
        ),
    )
    parser.add_argument(
        "artifact",
        nargs="?",
        choices=("sessions", "memories", "slots", "graph"),
        help="artifact to dump",
    )
    parser.add_argument("--memory-id", dest="memory_id", help="target memory_id for review-memory")
    parser.add_argument("--record-file", dest="record_file", help="JSON file containing the record")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = Path(args.project_root).resolve()

    try:
        if args.command == "paths":
            data = {k: str(v) if isinstance(v, Path) else v for k, v in asdict(resolve_memory_first_paths(project_root)).items()}
            _print_json(data)
            return 0

        if args.command == "synthesize-memories":
            created = synthesize_memories(project_root)
            _print_json({"created_count": len(created), "memory_ids": [item["memory_id"] for item in created]})
            return 0

        if args.command == "synthesize-slots":
            slots = synthesize_slots(project_root)
            _print_json({"slot_count": len(slots["slots"]), "slot_ids": [slot["slot_id"] for slot in slots["slots"]]})
            return 0

        if args.command == "synthesize-graph":
            edges = synthesize_graph(project_root)
            _print_json({"edge_count": len(edges), "edge_ids": [edge["edge_id"] for edge in edges]})
            return 0

        if args.command == "refresh-projections":
            _print_json(refresh_projections(project_root))
            return 0

        if args.command == "review-memory":
            if not args.memory_id:
                parser.error("review-memory requires --memory-id")
            if not args.record_file:
                parser.error("review-memory requires --record-file")
            record = _load_record_arg(args.record_file)
            updated = review_memory(project_root, args.memory_id, record)
            _print_json({"memory_id": updated["memory_id"], "status": updated["status"], "promotion_stage": updated["promotion_stage"]})
            return 0

        if args.command == "export":
            archive_path, playbook_path = export_surfaces(project_root)
            _print_json({"archive": str(archive_path), "playbook": str(playbook_path)})
            return 0

        if args.command == "materialize":
            _print_json(materialize_package(project_root))
            return 0

        if args.command == "dump":
            if args.artifact == "sessions":
                _print_json(load_sessions(project_root))
            elif args.artifact == "memories":
                _print_json(load_memories(project_root))
            elif args.artifact == "slots":
                _print_json(load_slots(project_root))
            elif args.artifact == "graph":
                _print_json(load_graph(project_root))
            else:
                parser.error("dump requires one artifact: sessions|memories|slots|graph")
            return 0

        if not args.record_file:
            parser.error(f"{args.command} requires --record-file")

        record = _load_record_arg(args.record_file)
        if args.command == "append-observation":
            append_observation(project_root, record)
        elif args.command == "append-session":
            append_session(project_root, record)
        elif args.command == "append-memory":
            append_memory(project_root, record)
        elif args.command == "append-graph":
            append_graph(project_root, record)
        elif args.command == "write-slots":
            write_slots(project_root, record)
        elif args.command == "upsert-slot":
            upsert_slot(project_root, record)
        else:
            parser.error(f"unsupported command: {args.command}")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
