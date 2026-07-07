from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_memory


def _copy_memory_first_fixture(tmp_path: Path) -> Path:
    dst = tmp_path / "memory_first_minimal"
    shutil.copytree(FIXTURES_DIR / "memory_first_minimal", dst)
    return dst


def test_resolve_memory_first_paths_uses_kind_layers(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)

    paths = mica_memory.resolve_memory_first_paths(fixture_root)

    assert paths.project_root == fixture_root
    assert paths.sessions == fixture_root / "memory" / "mica.sessions.jsonl"
    assert paths.memories == fixture_root / "memory" / "mica.memories.jsonl"
    assert paths.slots == fixture_root / "memory" / "mica.slots.json"
    assert paths.graph == fixture_root / "memory" / "mica.graph.jsonl"


def test_append_and_load_memory_first_records(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)

    session_record = {
        "schema_version": "mica.sessions.v1",
        "session_id": "sess_20260707_0002",
        "opened_at_utc": "2026-07-07T10:00:00Z",
        "closed_at_utc": "2026-07-07T10:30:00Z",
        "project_scope": "memory-first",
        "actors": [{"actor_id": "human_operator", "actor_type": "human"}],
        "source": {"system": "codex"},
        "session_hash": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    }
    memory_record = {
        "schema_version": "mica.memories.v1",
        "memory_id": "mem_0001",
        "created_at_utc": "2026-07-07T10:15:00Z",
        "updated_at_utc": "2026-07-07T10:15:00Z",
        "kind": "task_state",
        "status": "active",
        "project_scope": "memory-first",
        "summary": "The package has entered memory-first mode.",
        "source_event_ids": ["obs_0001"],
        "source_session_ids": ["sess_20260707_0002"],
        "trust_basis": "native_observation_trace",
        "promotion_stage": "candidate_memory",
        "slot_refs": [],
        "graph_refs": [],
    }
    graph_record = {
        "schema_version": "mica.graph.v1",
        "edge_id": "edge_0001",
        "from_ref": "mem_0001",
        "to_ref": "sess_20260707_0002",
        "relation": "belongs_to_session",
        "created_at_utc": "2026-07-07T10:16:00Z",
        "source_event_ids": ["obs_0001"],
    }
    slot_record = {
        "slot_id": "active_goal",
        "slot_kind": "active_goal",
        "value_ref": "mem_0001",
        "updated_at_utc": "2026-07-07T10:17:00Z",
        "stability": "stable",
        "source_memory_ids": ["mem_0001"],
    }

    mica_memory.append_session(fixture_root, session_record)
    mica_memory.append_memory(fixture_root, memory_record)
    mica_memory.append_graph(fixture_root, graph_record)
    mica_memory.upsert_slot(fixture_root, slot_record)

    sessions = mica_memory.load_sessions(fixture_root)
    memories = mica_memory.load_memories(fixture_root)
    graph = mica_memory.load_graph(fixture_root)
    slots = mica_memory.load_slots(fixture_root)

    assert sessions[-1]["session_id"] == "sess_20260707_0002"
    assert memories[-1]["memory_id"] == "mem_0001"
    assert graph[-1]["edge_id"] == "edge_0001"
    assert slots["slots"][-1]["slot_id"] == "active_goal"


def test_synthesize_memories_promotes_observations_once(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)

    observation_record = {
        "schema_version": "mica.observe.v1",
        "event_id": "obs_2001",
        "timestamp_utc": "2026-07-07T13:00:00Z",
        "session_id": "sess_20260707_0001",
        "hook": "file_edit",
        "scope": {"project": "memory-first", "paths": ["memory/mica_playbook.md"]},
        "summary": "Updated playbook export wording after memory-first migration.",
        "redaction": {"applied": False, "policy": "default"},
        "trust_tier": "native",
        "source_system": "codex",
        "event_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }

    mica_memory.append_observation(fixture_root, observation_record)

    created = mica_memory.synthesize_memories(fixture_root)
    created_again = mica_memory.synthesize_memories(fixture_root)
    memories = mica_memory.load_memories(fixture_root)

    assert len(created) == 1
    assert len(created_again) == 0
    assert memories[-1]["memory_id"] == "mem.obs.obs_2001"
    assert memories[-1]["kind"] == "task_state"
    assert memories[-1]["promotion_stage"] == "candidate_memory"
    assert memories[-1]["source_event_ids"] == ["obs_2001"]


def test_cli_paths_and_slots_dump(tmp_path: Path, capsys):
    fixture_root = _copy_memory_first_fixture(tmp_path)

    exit_code = mica_memory.main([str(fixture_root), "paths"])
    assert exit_code == 0
    paths_output = capsys.readouterr().out
    payload = json.loads(paths_output)
    assert payload["archive"].endswith("memory\\mica_archive.json")

    exit_code = mica_memory.main([str(fixture_root), "dump", "slots"])
    assert exit_code == 0
    slots_output = capsys.readouterr().out
    slots = json.loads(slots_output)
    assert slots["schema_version"] == "mica.slots.v1"


def test_cli_synthesize_memories_reports_created_ids(tmp_path: Path, capsys):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_observation(
        fixture_root,
        {
            "schema_version": "mica.observe.v1",
            "event_id": "obs_3001",
            "timestamp_utc": "2026-07-07T14:00:00Z",
            "session_id": "sess_20260707_0001",
            "hook": "operator_decision",
            "scope": {"project": "memory-first"},
            "summary": "Operator approved the first memory-first export boundary.",
            "redaction": {"applied": False, "policy": "default"},
            "trust_tier": "attested",
            "source_system": "codex",
            "event_hash": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        },
    )

    exit_code = mica_memory.main([str(fixture_root), "synthesize-memories"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["created_count"] == 1
    assert payload["memory_ids"] == ["mem.obs.obs_3001"]


def test_review_memory_promotes_candidate_to_approved_lesson(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_candidate_0001",
            "created_at_utc": "2026-07-07T16:00:00Z",
            "updated_at_utc": "2026-07-07T16:00:00Z",
            "kind": "task_state",
            "status": "active",
            "project_scope": "memory-first",
            "summary": "Candidate memory should become an approved lesson after review.",
            "source_event_ids": ["obs_1600"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "native_observation_trace",
            "promotion_stage": "candidate_memory",
            "slot_refs": [],
            "graph_refs": [],
        },
    )

    updated = mica_memory.review_memory(
        fixture_root,
        "mem_candidate_0001",
        {
            "decision": "approved_lesson",
            "reviewed_by": "human_operator",
            "reviewed_at_utc": "2026-07-07T16:05:00Z",
            "decision_reason": "Grounded and reusable as a lesson.",
        },
    )

    assert updated["kind"] == "lesson"
    assert updated["status"] == "approved"
    assert updated["promotion_stage"] == "approved_lesson"
    assert updated["operator_review"]["state"] == "approved"


def test_review_memory_promotes_candidate_to_bound_invariant_evidence(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_candidate_0002",
            "created_at_utc": "2026-07-07T17:00:00Z",
            "updated_at_utc": "2026-07-07T17:00:00Z",
            "kind": "constraint",
            "status": "active",
            "project_scope": "memory-first",
            "summary": "Candidate memory can bind an invariant when provenance is explicit.",
            "source_event_ids": ["obs_1700"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "attested_observation_trace",
            "promotion_stage": "candidate_memory",
            "slot_refs": [],
            "graph_refs": [],
        },
    )

    updated = mica_memory.review_memory(
        fixture_root,
        "mem_candidate_0002",
        {
            "decision": "bound_invariant_evidence",
            "reviewed_by": "human_operator",
            "reviewed_at_utc": "2026-07-07T17:10:00Z",
            "decision_reason": "Provenance is sufficient for binding evidence.",
            "origin_episode": "2026-07-07 production review",
            "supporting_event_ids": ["obs_1700"],
        },
    )

    assert updated["status"] == "promoted"
    assert updated["promotion_stage"] == "bound_invariant_evidence"
    assert updated["origin_episode"] == "2026-07-07 production review"
    assert updated["supporting_event_ids"] == ["obs_1700"]


def test_synthesize_slots_and_graph_from_memories(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_goal_0001",
            "created_at_utc": "2026-07-07T17:30:00Z",
            "updated_at_utc": "2026-07-07T17:35:00Z",
            "kind": "task_state",
            "status": "active",
            "project_scope": "memory-first",
            "summary": "Current active goal for the package.",
            "source_event_ids": ["obs_1735"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "native_observation_trace",
            "promotion_stage": "candidate_memory",
            "slot_refs": [],
            "graph_refs": [],
        },
    )
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_bound_0001",
            "created_at_utc": "2026-07-07T17:40:00Z",
            "updated_at_utc": "2026-07-07T17:45:00Z",
            "kind": "constraint",
            "status": "promoted",
            "project_scope": "memory-first",
            "summary": "Bound evidence should create invariant and graph projections.",
            "source_event_ids": ["obs_1740"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "native_observation_trace",
            "promotion_stage": "bound_invariant_evidence",
            "origin_episode": "2026-07-07 projection review",
            "supporting_event_ids": ["obs_1740"],
            "operator_review": {
                "state": "approved",
                "reviewed_by": "human_operator",
                "reviewed_at_utc": "2026-07-07T17:46:00Z",
                "decision_reason": "Projection-ready.",
            },
            "slot_refs": [],
            "graph_refs": [],
        },
    )

    slots = mica_memory.synthesize_slots(fixture_root)
    graph = mica_memory.synthesize_graph(fixture_root)

    slot_ids = {slot["slot_id"] for slot in slots["slots"]}
    edge_relations = {(edge["from_ref"], edge["to_ref"], edge["relation"]) for edge in graph}

    assert {"active_goal", "next_operator_decision", "current_invariant_set"} <= slot_ids
    assert ("mem_goal_0001", "sess_20260707_0001", "belongs_to_session") in edge_relations
    assert ("mem_bound_0001", "archive_export", "exported_as") in edge_relations
    assert ("mem_bound_0001", "obs_1740", "supports") in edge_relations


def test_review_memory_blocks_opaque_binding_promotion(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_candidate_opaque",
            "created_at_utc": "2026-07-07T18:00:00Z",
            "updated_at_utc": "2026-07-07T18:00:00Z",
            "kind": "constraint",
            "status": "active",
            "project_scope": "memory-first",
            "summary": "Opaque memory must not become binding evidence.",
            "source_event_ids": ["obs_1800"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "opaque_observation_trace",
            "promotion_stage": "candidate_memory",
            "slot_refs": [],
            "graph_refs": [],
        },
    )

    with pytest.raises(ValueError, match="opaque_observation_trace"):
        mica_memory.review_memory(
            fixture_root,
            "mem_candidate_opaque",
            {
                "decision": "bound_invariant_evidence",
                "reviewed_by": "human_operator",
                "reviewed_at_utc": "2026-07-07T18:05:00Z",
                "decision_reason": "Should fail.",
                "origin_episode": "2026-07-07 failed review",
                "supporting_event_ids": ["obs_1800"],
            },
        )


def test_export_surfaces_writes_archive_and_playbook_from_memories(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    archive_seed = json.loads((fixture_root / "memory" / "mica_archive.json").read_text(encoding="utf-8"))
    archive_seed["design_invariants"] = [
        {
            "id": "DI-001",
            "label": "manual-invariant",
            "statement": "Manual DI should survive exporter reruns.",
            "severity": "critical",
        }
    ]
    (fixture_root / "memory" / "mica_archive.json").write_text(
        json.dumps(archive_seed, indent=2),
        encoding="utf-8",
    )

    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_lesson_0001",
            "created_at_utc": "2026-07-07T11:00:00Z",
            "updated_at_utc": "2026-07-07T11:10:00Z",
            "kind": "lesson",
            "status": "approved",
            "project_scope": "memory-first",
            "summary": "Archive exports must come from approved memory, not raw observation.",
            "source_event_ids": ["obs_1001"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "native_observation_trace",
            "promotion_stage": "approved_lesson",
            "slot_refs": [],
            "graph_refs": [],
        },
    )
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_bind_0001",
            "created_at_utc": "2026-07-07T11:20:00Z",
            "updated_at_utc": "2026-07-07T11:30:00Z",
            "kind": "constraint",
            "status": "promoted",
            "project_scope": "memory-first",
            "summary": "Promoted binding evidence must preserve source event references.",
            "source_event_ids": ["obs_1002"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "attested_observation_trace",
            "promotion_stage": "bound_invariant_evidence",
            "origin_episode": "2026-07-07 promotion review",
            "supporting_event_ids": ["obs_1002"],
            "operator_review": {
                "state": "approved",
                "reviewed_by": "human_operator",
                "reviewed_at_utc": "2026-07-07T11:31:00Z",
                "decision_reason": "Binding evidence accepted.",
            },
            "di_id": "DI-MEM-900",
            "di_label": "preserve-source-event-refs",
            "di_statement": "Promoted binding evidence must preserve source event references.",
            "severity": "critical",
            "slot_refs": [],
            "graph_refs": [],
        },
    )

    archive_path, playbook_path = mica_memory.export_surfaces(fixture_root)
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    playbook = playbook_path.read_text(encoding="utf-8")

    assert archive["operation_meta"]["last_updated"] == "2026-07-07"
    assert len(archive["memory_exports"]) == 2
    assert len(archive["design_invariants"]) == 2
    assert archive["design_invariants"][0]["id"] == "DI-001"
    assert archive["design_invariants"][1]["id"] == "DI-MEM-900"
    assert archive["design_invariants"][1]["binding"]["origin_episode"] == "2026-07-07 promotion review"
    assert archive["design_invariants"][1]["source_memory_id"] == "mem_bind_0001"
    assert archive["memory_exports"][0]["memory_id"] == "mem_lesson_0001"
    assert archive["memory_exports"][1]["memory_id"] == "mem_bind_0001"
    assert "Approved Lessons" in playbook
    assert "mem_lesson_0001" in playbook
    assert "Archive exports must come from approved memory" in playbook


def test_cli_export_reports_written_paths(tmp_path: Path, capsys):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_export_0001",
            "created_at_utc": "2026-07-07T12:00:00Z",
            "updated_at_utc": "2026-07-07T12:01:00Z",
            "kind": "lesson",
            "status": "approved",
            "project_scope": "memory-first",
            "summary": "CLI export should materialize archive and playbook surfaces.",
            "source_event_ids": ["obs_1200"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "native_observation_trace",
            "promotion_stage": "approved_lesson",
            "slot_refs": [],
            "graph_refs": [],
        },
    )

    exit_code = mica_memory.main([str(fixture_root), "export"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["archive"].endswith("memory\\mica_archive.json")
    assert payload["playbook"].endswith("memory\\mica_playbook.md")


def test_review_then_export_generates_design_invariant(tmp_path: Path):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_bind_export_0001",
            "created_at_utc": "2026-07-07T21:00:00Z",
            "updated_at_utc": "2026-07-07T21:00:00Z",
            "kind": "constraint",
            "status": "active",
            "project_scope": "memory-first",
            "summary": "Binding export must synthesize a DI entry.",
            "source_event_ids": ["obs_2100"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "native_observation_trace",
            "promotion_stage": "candidate_memory",
            "slot_refs": [],
            "graph_refs": [],
        },
    )

    mica_memory.review_memory(
        fixture_root,
        "mem_bind_export_0001",
        {
            "decision": "bound_invariant_evidence",
            "reviewed_by": "human_operator",
            "reviewed_at_utc": "2026-07-07T21:10:00Z",
            "decision_reason": "Ready for DI export.",
            "origin_episode": "2026-07-07 binding review",
            "supporting_event_ids": ["obs_2100"],
        },
    )

    archive = mica_memory.build_archive_export(fixture_root)
    generated = [item for item in archive["design_invariants"] if item.get("source_memory_id") == "mem_bind_export_0001"]
    assert len(generated) == 1
    assert generated[0]["id"] == "DI-MEM-001"
    assert generated[0]["statement"] == "Binding export must synthesize a DI entry."


def test_cli_review_memory_reports_updated_stage(tmp_path: Path, capsys):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_cli_review_0001",
            "created_at_utc": "2026-07-07T19:00:00Z",
            "updated_at_utc": "2026-07-07T19:00:00Z",
            "kind": "task_state",
            "status": "active",
            "project_scope": "memory-first",
            "summary": "CLI review should update promotion stage.",
            "source_event_ids": ["obs_1900"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "native_observation_trace",
            "promotion_stage": "candidate_memory",
            "slot_refs": [],
            "graph_refs": [],
        },
    )
    review_file = fixture_root / "review.json"
    review_file.write_text(
        json.dumps(
            {
                "decision": "approved_lesson",
                "reviewed_by": "human_operator",
                "reviewed_at_utc": "2026-07-07T19:10:00Z",
                "decision_reason": "CLI review path validated.",
            }
        ),
        encoding="utf-8",
    )

    exit_code = mica_memory.main(
        [
            str(fixture_root),
            "review-memory",
            "--memory-id",
            "mem_cli_review_0001",
            "--record-file",
            str(review_file),
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["memory_id"] == "mem_cli_review_0001"
    assert payload["status"] == "approved"
    assert payload["promotion_stage"] == "approved_lesson"
    memories = mica_memory.load_memories(fixture_root)
    assert memories[-1]["kind"] == "lesson"
    assert memories[-1]["operator_review"]["state"] == "approved"


def test_cli_refresh_projections_reports_counts(tmp_path: Path, capsys):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_memory(
        fixture_root,
        {
            "schema_version": "mica.memories.v1",
            "memory_id": "mem_proj_cli_0001",
            "created_at_utc": "2026-07-07T19:20:00Z",
            "updated_at_utc": "2026-07-07T19:21:00Z",
            "kind": "task_state",
            "status": "active",
            "project_scope": "memory-first",
            "summary": "Projection CLI should count slots and edges.",
            "source_event_ids": ["obs_1920"],
            "source_session_ids": ["sess_20260707_0001"],
            "trust_basis": "native_observation_trace",
            "promotion_stage": "candidate_memory",
            "slot_refs": [],
            "graph_refs": [],
        },
    )

    exit_code = mica_memory.main([str(fixture_root), "refresh-projections"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["slot_count"] >= 1
    assert payload["edge_count"] >= 1


def test_cli_materialize_runs_end_to_end(tmp_path: Path, capsys):
    fixture_root = _copy_memory_first_fixture(tmp_path)
    mica_memory.append_observation(
        fixture_root,
        {
            "schema_version": "mica.observe.v1",
            "event_id": "obs_mat_0001",
            "timestamp_utc": "2026-07-07T20:00:00Z",
            "session_id": "sess_20260707_0001",
            "hook": "operator_decision",
            "scope": {"project": "memory-first", "paths": ["memory/mica_archive.json"]},
            "summary": "Materialize should rebuild derived package artifacts from live memory state.",
            "redaction": {"applied": False, "policy": "default"},
            "trust_tier": "native",
            "source_system": "codex",
            "event_hash": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        },
    )

    exit_code = mica_memory.main([str(fixture_root), "materialize"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["created_memory_count"] == 1
    assert payload["created_memory_ids"] == ["mem.obs.obs_mat_0001"]
    assert payload["slot_count"] >= 1
    assert payload["edge_count"] >= 1
    assert Path(payload["archive"]).exists()
    assert Path(payload["playbook"]).exists()
