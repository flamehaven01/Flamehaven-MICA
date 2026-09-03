"""P1 coverage for digest-bound invocation evidence (mica.invocation.v2).

Each negative test corresponds to a failure class named in
docs/MICA_v3.0.0_CONTEXT_CONTINUITY_PLAN.md section 10 (P1).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core  # noqa: E402
import mica_runtime  # noqa: E402

FIXTURE = REPO_ROOT / "fixtures" / "memory_first_minimal"


def _write_record(tmp_path: Path, record: dict) -> Path:
    path = tmp_path / "mica.invocation.jsonl"
    path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _statuses(results: list[tuple[str, str, str]]) -> dict[str, tuple[str, str]]:
    return {pid: (status, msg) for pid, status, msg in results}


def _base_record() -> dict:
    summary = mica_runtime.build_summary(FIXTURE)
    return mica_runtime.build_invocation_trace_record(
        summary, trigger={"kind": "review", "ref": "git:deadbeef"}
    )


# --- positive baseline -------------------------------------------------------


def test_capsule_record_is_digest_bound_and_valid(tmp_path: Path):
    record = _base_record()
    path = _write_record(tmp_path, record)

    assert record["schema_version"] == "mica.invocation.v2"
    assert record["trigger"] == {"kind": "review", "ref": "git:deadbeef"}
    assert record["surface_evidence"], "expected evidence for loaded surfaces"

    for entry in record["surface_evidence"]:
        assert entry["sha256"].startswith("sha256:")
        assert len(entry["sha256"]) == len("sha256:") + 64
        assert entry["bytes"] >= 0
        assert entry["delivery_state"] == "resolved"
        assert "\\" not in entry["path"]
        assert not entry["path"].startswith("/")

    results = _statuses(mica_core.run_invocation_trace_checks(path))
    assert results["IVC-003"][0] == "PASS"
    assert results["IVC-004"][0] == "PASS"


def test_v1_records_remain_valid(tmp_path: Path):
    """v2 support must not invalidate history written under v1."""
    record = _base_record()
    for field in ("trigger", "surface_evidence", "capsule_hash"):
        record.pop(field, None)
    record["schema_version"] = "mica.invocation.v1"

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-003"][0] == "PASS"
    assert results["IVC-004"][0] == "PASS"


# --- negative: hash determinism ---------------------------------------------


def test_capsule_hash_is_deterministic_and_excludes_project_root():
    record = _base_record()
    first = mica_core.compute_capsule_hash(record)

    reordered = dict(reversed(list(record.items())))
    assert mica_core.compute_capsule_hash(reordered) == first

    # project_root is absolute and machine-specific; it must not affect the hash.
    relocated = dict(record, project_root="/somewhere/else")
    assert mica_core.compute_capsule_hash(relocated) == first


def test_capsule_hash_mismatch_is_detected(tmp_path: Path):
    record = _base_record()
    record["surface_evidence"][0]["bytes"] += 1

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-004"][0] == "FAIL"
    assert "capsule_hash mismatch" in results["IVC-004"][1]


# --- negative: audience separation ------------------------------------------


def test_operator_only_surface_cannot_be_labeled_agent_context(tmp_path: Path):
    record = _base_record()
    record["operator_only_surfaces"] = ["observations"]
    for entry in record["surface_evidence"]:
        if entry["role"] == "observations":
            entry["audience"] = "agent_context"
    record["capsule_hash"] = mica_core.compute_capsule_hash(record)

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-004"][0] == "FAIL"
    assert "recorded as agent_context evidence" in results["IVC-004"][1]


def test_agent_context_label_requires_membership(tmp_path: Path):
    record = _base_record()
    for entry in record["surface_evidence"]:
        if entry["role"] == "observations":
            entry["audience"] = "agent_context"
    record["capsule_hash"] = mica_core.compute_capsule_hash(record)

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-004"][0] == "FAIL"
    assert "absent from agent_context_surfaces" in results["IVC-004"][1]


def test_evidence_role_must_be_loaded(tmp_path: Path):
    record = _base_record()
    record["surface_evidence"].append(
        {
            "role": "never_loaded",
            "path": "memory/ghost.json",
            "sha256": "sha256:" + "0" * 64,
            "bytes": 0,
            "audience": "operator_only",
            "delivery_state": "resolved",
        }
    )
    record["capsule_hash"] = mica_core.compute_capsule_hash(record)

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-004"][0] == "FAIL"
    assert "not in loaded_surfaces" in results["IVC-004"][1]


# --- negative: path hygiene --------------------------------------------------


@pytest.mark.parametrize(
    "bad_path, reason",
    [
        ("memory\\mica_archive.json", "forward slashes"),
        ("/abs/memory/mica_archive.json", "repository-relative"),
        ("C:/memory/mica_archive.json", "repository-relative"),
        ("../outside/mica_archive.json", "escape the project root"),
    ],
)
def test_non_canonical_paths_are_rejected(tmp_path: Path, bad_path: str, reason: str):
    record = _base_record()
    record["surface_evidence"][0]["path"] = bad_path
    record["capsule_hash"] = mica_core.compute_capsule_hash(record)

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-003"][0] == "FAIL"
    assert reason in results["IVC-003"][1]


def test_duplicate_roles_and_paths_are_rejected(tmp_path: Path):
    record = _base_record()
    record["surface_evidence"].append(dict(record["surface_evidence"][0]))
    record["capsule_hash"] = mica_core.compute_capsule_hash(record)

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-003"][0] == "FAIL"
    assert "duplicate role" in results["IVC-003"][1]


def test_canonical_surface_path_rejects_escape(tmp_path: Path):
    outside = tmp_path.parent / "outside.json"
    outside.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="escapes project root"):
        mica_core.canonical_surface_path(tmp_path, outside)


def test_canonical_surface_path_normalizes_separators(tmp_path: Path):
    nested = tmp_path / "memory" / "sub"
    nested.mkdir(parents=True)
    target = nested / "archive.json"
    target.write_text("{}", encoding="utf-8")

    assert mica_core.canonical_surface_path(tmp_path, target) == "memory/sub/archive.json"


# --- negative: overclaim -----------------------------------------------------


def test_null_session_cannot_claim_delivery(tmp_path: Path):
    record = _base_record()
    record["session_id"] = None
    record["surface_evidence"][0]["delivery_state"] = "emitted"
    record["capsule_hash"] = mica_core.compute_capsule_hash(record)

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-004"][0] == "FAIL"
    assert "null session_id cannot claim delivery" in results["IVC-004"][1]


def test_null_session_may_still_record_resolution(tmp_path: Path):
    record = _base_record()
    record["session_id"] = None
    record["capsule_hash"] = mica_core.compute_capsule_hash(record)

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-004"][0] == "PASS"


def test_invalid_delivery_state_is_rejected(tmp_path: Path):
    record = _base_record()
    record["surface_evidence"][0]["delivery_state"] = "understood"
    record["capsule_hash"] = mica_core.compute_capsule_hash(record)

    results = _statuses(mica_core.run_invocation_trace_checks(_write_record(tmp_path, record)))

    assert results["IVC-003"][0] == "FAIL"
    assert "invalid delivery_state" in results["IVC-003"][1]


# --- negative: resolve-to-emit drift ----------------------------------------


def test_surface_mutation_between_resolution_and_emission_is_refused(tmp_path: Path):
    project_root = tmp_path / "pkg"
    memory_dir = project_root / "memory"
    memory_dir.mkdir(parents=True)
    (project_root / "mica.yaml").write_text(
        "\n".join(
            [
                "mica_spec: '0.2.8'",
                "name: drift-fixture",
                "mode: memory_injection",
                "layers:",
                "  - id: archive",
                "    kind: archive",
                "    path: memory/mica_archive.json",
                "  - id: playbook",
                "    kind: playbook",
                "    path: memory/mica_playbook.md",
            ]
        ),
        encoding="utf-8",
    )
    (memory_dir / "mica_playbook.md").write_text("# playbook\n", encoding="utf-8")
    archive_path = memory_dir / "mica_archive.json"
    archive_path.write_text(
        json.dumps(
            {
                "mica_spec": "0.2.8",
                "project": {"name": "drift-fixture", "version": "1.0.0"},
                "design_invariants": [],
                "operation_meta": {"last_updated": "2026-09-03"},
            }
        ),
        encoding="utf-8",
    )

    summary = mica_runtime.build_summary(project_root)
    assert summary["surface_evidence"], "expected resolved evidence before mutation"

    # The surface changes after resolution but before the trace is written.
    archive_path.write_text(
        json.dumps(
            {
                "mica_spec": "0.2.8",
                "project": {"name": "drift-fixture", "version": "1.0.1"},
                "design_invariants": [],
                "operation_meta": {"last_updated": "2026-09-03"},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="changed between resolution and emission"):
        mica_runtime.write_invocation_trace(
            project_root, summary, tmp_path / "mica.invocation.jsonl"
        )


def test_missing_surface_between_resolution_and_emission_is_refused(tmp_path: Path):
    summary = mica_runtime.build_summary(FIXTURE)
    summary["surface_evidence"] = [
        {
            "role": "archive",
            "path": "memory/does_not_exist.json",
            "sha256": "sha256:" + "0" * 64,
            "bytes": 0,
            "audience": "agent_context",
            "delivery_state": "resolved",
        }
    ]

    with pytest.raises(RuntimeError, match="changed between resolution and emission"):
        mica_runtime.write_invocation_trace(FIXTURE, summary, tmp_path / "mica.invocation.jsonl")


# --- committed fixture -------------------------------------------------------


def test_committed_capsule_fixture_still_matches_its_surfaces():
    """The fixture's recorded digests must match the fixture's bytes on disk.

    This deliberately fails if fixture surfaces are edited without regenerating
    the trace, which is the drift class the capsule exists to detect.
    """
    fixture = REPO_ROOT / "fixtures" / "invocation_capsule_v2"
    trace = fixture / "memory" / "mica.invocation.jsonl"

    results = _statuses(mica_core.run_invocation_trace_checks(trace))

    assert results["IVC-003"][0] == "PASS"
    assert results["IVC-004"][0] == "PASS", results["IVC-004"][1]

    record = json.loads(trace.read_text(encoding="utf-8").strip())
    assert record["schema_version"] == "mica.invocation.v2"
    for entry in record["surface_evidence"]:
        digest, size = mica_core.hash_surface_bytes(fixture / entry["path"])
        assert digest == entry["sha256"]
        assert size == entry["bytes"]
