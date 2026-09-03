#!/usr/bin/env python3
"""
MICA flow plane -- memory-authoring pipeline checks.

Producing memory is a different job from invoking it. These checks cover the
observe -> candidate -> promotion pipeline and the recall trace: whether the
observation chain is coherent, whether promoted artifacts carry provenance,
whether recall telemetry joins, and whether anything unapproved reached
agent context.

Only PCT-017 sits on the invocation contract axis, because it asks what entered
agent_context. The rest report on the flow axis and never break the contract.

Extracted from mica_core.py at v3.0.0 Origin P3a. mica_core.py had grown to
1,893 lines with a deficit score of 68.2; these 485 lines were one critical and
five high findings inside it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mica_primitives import (
    _is_non_empty_string,
    _normalized_json_text,
    find_flow_artifact,
    load_json,
    load_jsonl,
)

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


def compute_observation_event_hash(record: dict[str, Any]) -> str:
    payload = {k: v for k, v in record.items() if k != "event_hash"}
    digest = hashlib.sha256(_normalized_json_text(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


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
            return (
                "PCT-013",
                "FAIL",
                f"record {index} has unsupported schema_version: {record.get('schema_version')}",
            )
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
                return (
                    "PCT-013",
                    "FAIL",
                    f"record {index} unexpectedly declares prev_event_hash at stream head",
                )
        elif prev_hash != previous_hash:
            return ("PCT-013", "FAIL", f"record {index} prev_event_hash mismatch for {event_id}")
        previous_hash = str(record.get("event_hash"))
        timestamp = record.get("timestamp_utc")
        if (
            _is_non_empty_string(previous_timestamp)
            and _is_non_empty_string(timestamp)
            and str(timestamp) < str(previous_timestamp)
        ):
            timestamp_regressed = True
        previous_timestamp = str(timestamp)

    if timestamp_regressed:
        return (
            "PCT-013",
            "WARN",
            f"{observe_path.relative_to(project_root)} coherent but timestamps are not monotonic",
        )
    return (
        "PCT-013",
        "PASS",
        f"{observe_path.relative_to(project_root)} parseable and hash-chain coherent ({len(records)} records)",
    )


def _run_pct015(project_root: Path, flow_policy: dict[str, Any]) -> tuple[str, str, str]:
    if not _flow_enabled(flow_policy):
        return ("PCT-015", "INFO", "flow disabled; promotion provenance not required")

    candidates_path = find_flow_artifact(project_root, "mica.candidates.json")
    if not candidates_path:
        return ("PCT-015", "FAIL", "flow enabled but mica.candidates.json missing")
    candidates_doc = load_json(candidates_path)
    if candidates_doc.get("schema_version") != "mica.candidates.v1":
        return (
            "PCT-015",
            "FAIL",
            f"candidate registry has unsupported schema_version: {candidates_doc.get('schema_version')}",
        )
    candidates = candidates_doc.get("candidates")
    if not isinstance(candidates, list):
        return ("PCT-015", "FAIL", "candidate registry missing candidates list")
    observe_path = find_flow_artifact(project_root, "mica.observe.jsonl")
    if not observe_path:
        return (
            "PCT-015",
            "FAIL",
            "cannot validate promotion provenance because mica.observe.jsonl is missing",
        )
    observations = load_jsonl(observe_path)
    observation_ids = {
        record.get("event_id")
        for record in observations
        if _is_non_empty_string(record.get("event_id"))
    }
    governed = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return ("PCT-015", "FAIL", "candidate registry contains a non-object item")
        if candidate.get("stage") in {"approved_lesson", "bound_invariant_evidence"}:
            governed.append(candidate)
    if not governed:
        return (
            "PCT-015",
            "INFO",
            f"{candidates_path.relative_to(project_root)} contains no approved or promoted artifacts requiring provenance validation",
        )

    issues: list[str] = []
    for candidate in governed:
        candidate_id = str(candidate.get("candidate_id") or "?")
        source_event_ids = candidate.get("source_event_ids")
        if not isinstance(source_event_ids, list) or not source_event_ids:
            issues.append(f"{candidate_id}: missing source_event_ids")
        else:
            missing_source_ids = [
                source_id for source_id in source_event_ids if source_id not in observation_ids
            ]
            if missing_source_ids:
                issues.append(f"{candidate_id}: unknown source_event_ids {missing_source_ids}")
        if not _review_is_approved(candidate.get("operator_review")):
            issues.append(
                f"{candidate_id}: operator_review must be approved with non-null review metadata"
            )
        if candidate.get("stage") == "bound_invariant_evidence":
            if not _is_non_empty_string(candidate.get("origin_episode")):
                issues.append(f"{candidate_id}: missing origin_episode")
            supporting_event_ids = candidate.get("supporting_event_ids")
            if not isinstance(supporting_event_ids, list) or not supporting_event_ids:
                issues.append(f"{candidate_id}: missing supporting_event_ids")
            else:
                missing_support_ids = [
                    event_id for event_id in supporting_event_ids if event_id not in observation_ids
                ]
                if missing_support_ids:
                    issues.append(
                        f"{candidate_id}: unknown supporting_event_ids {missing_support_ids}"
                    )
            if candidate.get("trust_basis") == "opaque_observation_trace":
                issues.append(f"{candidate_id}: Stage 3 evidence may not use opaque trust_basis")
    if issues:
        preview = "; ".join(issues[:4])
        if len(issues) > 4:
            preview += f"; ... (+{len(issues) - 4} more)"
        return ("PCT-015", "FAIL", preview)
    return (
        "PCT-015",
        "PASS",
        f"validated promotion provenance for {len(governed)} governed candidate(s)",
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
        return (
            "PCT-014",
            "WARN",
            f"{recall_path.relative_to(project_root)} empty while recall is active",
        )

    issues: list[str] = []
    for index, record in enumerate(records, start=1):
        if record.get("schema_version") != "mica.recall.v1":
            issues.append(
                f"record {index}: unsupported schema_version {record.get('schema_version')}"
            )
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
    return (
        "PCT-014",
        "PASS",
        f"{recall_path.relative_to(project_root)} provides recall trace coverage ({len(records)} records)",
    )


def _run_pct018(project_root: Path, flow_policy: dict[str, Any]) -> tuple[str, str, str]:
    if not _flow_enabled(flow_policy):
        return ("PCT-018", "INFO", "flow disabled; telemetry completeness not required")

    recall_path = find_flow_artifact(project_root, "mica.recall.jsonl")
    if not recall_path:
        return ("PCT-018", "INFO", "recall trace absent; telemetry completeness not active")

    observe_path = find_flow_artifact(project_root, "mica.observe.jsonl")
    candidates_path = find_flow_artifact(project_root, "mica.candidates.json")
    invocation_path = find_flow_artifact(project_root, "mica.invocation.jsonl")
    try:
        observations = load_jsonl(observe_path)
    except Exception as exc:
        return (
            "PCT-018",
            "WARN",
            f"cannot load observation stream for telemetry completeness: {exc}",
        )
    candidates_doc = load_json(candidates_path)
    candidates = (
        candidates_doc.get("candidates")
        if isinstance(candidates_doc.get("candidates"), list)
        else []
    )
    try:
        recall_records = load_jsonl(recall_path)
    except Exception as exc:
        return ("PCT-018", "WARN", f"cannot load recall trace for telemetry completeness: {exc}")
    if not recall_records:
        return (
            "PCT-018",
            "INFO",
            "recall trace empty; completeness deferred to PCT-014 coverage warning",
        )

    invocation_records: list[dict[str, Any]] = []
    if invocation_path:
        try:
            invocation_records = load_jsonl(invocation_path)
        except Exception as exc:
            return (
                "PCT-018",
                "WARN",
                f"cannot load invocation trace for telemetry completeness: {exc}",
            )

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
    invocation_by_session = {
        record.get("session_id"): record
        for record in invocation_records
        if isinstance(record, dict) and _is_non_empty_string(record.get("session_id"))
    }

    issues: list[str] = []
    for index, record in enumerate(recall_records, start=1):
        candidate_id = record.get("candidate_id")
        if not _is_non_empty_string(candidate_id):
            issues.append(f"record {index}: missing candidate_id")
            continue
        candidate = candidate_map.get(candidate_id)
        if not isinstance(candidate, dict):
            issues.append(
                f"record {index}: candidate_id {candidate_id} not found in mica.candidates.json"
            )
            continue

        session_id = record.get("session_id")
        if not _is_non_empty_string(session_id) or session_id not in observation_sessions:
            issues.append(
                f"record {index}: session_id {session_id!r} not linked to observation stream"
            )

        source_event_ids = record.get("source_event_ids")
        if not isinstance(source_event_ids, list) or not source_event_ids:
            issues.append(f"record {index}: missing source_event_ids for candidate {candidate_id}")
            continue

        missing_observation_ids = [
            event_id for event_id in source_event_ids if event_id not in observation_ids
        ]
        if missing_observation_ids:
            issues.append(
                f"record {index}: source_event_ids not found in observation stream: {missing_observation_ids}"
            )

        candidate_source_ids = candidate.get("source_event_ids")
        if isinstance(candidate_source_ids, list):
            extra_ids = [
                event_id for event_id in source_event_ids if event_id not in candidate_source_ids
            ]
            if extra_ids:
                issues.append(
                    f"record {index}: source_event_ids not declared on candidate {candidate_id}: {extra_ids}"
                )

        target = record.get("target")
        if target == "agent_context":
            if not invocation_path:
                issues.append(
                    f"record {index}: target=agent_context but mica.invocation.jsonl absent"
                )
                continue
            invocation = invocation_by_session.get(session_id)
            if not isinstance(invocation, dict):
                issues.append(
                    f"record {index}: session_id {session_id!r} not linked to invocation trace"
                )
                continue
            loaded_surfaces = invocation.get("loaded_surfaces")
            if not isinstance(loaded_surfaces, list) or not loaded_surfaces:
                issues.append(
                    f"record {index}: invocation trace missing loaded_surfaces for session {session_id}"
                )
            context_surfaces = invocation.get("agent_context_surfaces")
            if not isinstance(context_surfaces, list) or not context_surfaces:
                issues.append(
                    f"record {index}: invocation trace missing agent_context_surfaces for session {session_id}"
                )
            elif isinstance(loaded_surfaces, list):
                extra_context = [
                    surface for surface in context_surfaces if surface not in loaded_surfaces
                ]
                if extra_context:
                    issues.append(
                        f"record {index}: invocation trace agent_context_surfaces not loaded for session {session_id}: {extra_context}"
                    )
        elif target == "operator_review" and invocation_path:
            invocation = invocation_by_session.get(session_id)
            if not isinstance(invocation, dict):
                issues.append(
                    f"record {index}: operator_review session_id {session_id!r} not linked to invocation trace"
                )
                continue
            operator_surfaces = invocation.get("operator_only_surfaces")
            if not isinstance(operator_surfaces, list) or not operator_surfaces:
                issues.append(
                    f"record {index}: invocation trace missing operator_only_surfaces for operator_review session {session_id}"
                )

    if issues:
        preview = "; ".join(issues[:4])
        if len(issues) > 4:
            preview += f"; ... (+{len(issues) - 4} more)"
        return ("PCT-018", "WARN", preview)
    if invocation_path:
        return (
            "PCT-018",
            "PASS",
            f"{recall_path.relative_to(project_root)} joins cleanly with candidates, observations, and invocation trace",
        )
    return (
        "PCT-018",
        "PASS",
        f"{recall_path.relative_to(project_root)} joins cleanly with candidates and observations",
    )


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
        return (
            "PCT-017",
            "INFO",
            "recall enabled but trace file absent; PCT-017 deferred until runtime trace exists",
        )

    candidates_path = find_flow_artifact(project_root, "mica.candidates.json")
    candidates_doc = load_json(candidates_path)
    candidates = (
        candidates_doc.get("candidates")
        if isinstance(candidates_doc.get("candidates"), list)
        else []
    )
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
        return (
            "PCT-017",
            "INFO",
            f"{recall_path.relative_to(project_root)} empty; no recall injection recorded",
        )

    inject_unapproved = bool(recall_policy.get("inject_unapproved_candidates", False))
    issues: list[str] = []
    for index, record in enumerate(records, start=1):
        if record.get("schema_version") != "mica.recall.v1":
            issues.append(
                f"record {index}: unsupported schema_version {record.get('schema_version')}"
            )
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
            review = (
                candidate.get("operator_review")
                if isinstance(candidate.get("operator_review"), dict)
                else {}
            )
            review_state = review.get("state") or "unknown"
            issues.append(
                f"candidate {candidate_id} entered agent_context while operator_review.state={review_state}"
            )

    if issues:
        preview = "; ".join(issues[:4])
        if len(issues) > 4:
            preview += f"; ... (+{len(issues) - 4} more)"
        return ("PCT-017", "FAIL", preview)
    return (
        "PCT-017",
        "PASS",
        f"{recall_path.relative_to(project_root)} enforces approved-only agent_context injection",
    )


# ---------------------------------------------------------------------------
# PCT checks
# ---------------------------------------------------------------------------
