from __future__ import annotations

import json
import sys
from textwrap import dedent
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core
import mica_pct
import mica_runtime


def _write_archive(path: Path, version: str, last_updated: str) -> None:
    payload = {
        "project": {"name": "fixture", "version": version},
        "operation_meta": {"last_updated": last_updated},
        "design_invariants": [],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_tool_versions_are_aligned():
    assert mica_core.MICA_TOOL_VERSION == "0.2.8"
    assert mica_pct.__version__ == mica_core.MICA_TOOL_VERSION
    assert mica_runtime.__version__ == mica_core.MICA_TOOL_VERSION
    assert mica_core.format_tool_banner("MICA PCT Validator") == "MICA PCT Validator v0.2.8"


def test_find_legacy_archive_prefers_highest_version(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    older = memory_dir / "fixture.mica.v1.2.0.json"
    newer = memory_dir / "fixture.mica.v1.10.0.json"
    _write_archive(older, "1.2.0", "2026-06-01")
    _write_archive(newer, "1.10.0", "2026-01-01")

    selected = mica_core.find_legacy_archive(tmp_path)

    assert selected == newer


def test_find_legacy_archive_uses_last_updated_as_tiebreaker(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    first = memory_dir / "alpha.mica.v1.0.0.json"
    second = memory_dir / "beta.mica.v1.0.0.json"
    _write_archive(first, "1.0.0", "2026-01-15")
    _write_archive(second, "1.0.0", "2026-06-30")

    selected = mica_core.find_legacy_archive(tmp_path)

    assert selected == second


def test_schema_supports_memory_first_mode():
    schema = json.loads((REPO_ROOT / "mica.yaml.schema.json").read_text(encoding="utf-8"))

    assert "memory_first" in schema["properties"]["mode"]["enum"]
    assert "memory_policy" in schema["properties"]
    assert "flow_policy" in schema["properties"]
    assert "recall_policy" in schema["properties"]
    assert "promotion_policy" in schema["properties"]
    assert "kind" in schema["$defs"]["layer"]["properties"]
    assert "agent_context_surfaces" in schema["$defs"]["invocationProtocol"]["properties"]


def test_memory_first_record_schemas_exist_and_expose_expected_versions():
    expected = {
        "mica.sessions.schema.json": ("Session", "mica.sessions.v1"),
        "mica.memories.schema.json": ("Memory", "mica.memories.v1"),
        "mica.slots.schema.json": ("Slot", "mica.slots.v1"),
        "mica.graph.schema.json": ("Graph", "mica.graph.v1"),
    }

    for filename, (title_fragment, version_const) in expected.items():
        schema = json.loads((REPO_ROOT / filename).read_text(encoding="utf-8"))
        assert title_fragment in schema["title"]
        if filename == "mica.slots.schema.json":
            assert schema["properties"]["schema_version"]["const"] == version_const
        else:
            assert schema["properties"]["schema_version"]["const"] == version_const


def test_memory_first_contract_is_closed_and_resolves_export_paths(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (tmp_path / "mica.yaml").write_text(
        dedent(
            """
            mica_spec: "0.2.9"
            mode: memory_first
            memory_policy:
              primary_store: memory/
              session_capture: true
              observation_append_only: true
              memory_exports_required: true
              slot_projection_enabled: true
            flow_policy:
              enabled: false
            layers:
              - id: sessions
                kind: sessions
                path: memory/mica.sessions.jsonl
              - id: observe
                kind: observations
                path: memory/mica.observe.jsonl
              - id: memories
                kind: memories
                path: memory/mica.memories.jsonl
              - id: slots
                kind: slots
                path: memory/mica.slots.json
              - id: archive_export
                kind: archive
                path: memory/mica_archive.json
              - id: playbook_export
                kind: playbook
                path: memory/mica_playbook.md
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (memory_dir / "mica.sessions.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.observe.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.memories.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.slots.json").write_text('{"schema_version":"mica.slots.v1","slots":[]}', encoding="utf-8")
    (memory_dir / "mica_playbook.md").write_text("# playbook\n", encoding="utf-8")
    (memory_dir / "mica_archive.json").write_text(
        json.dumps(
            {
                "mica_spec": "0.2.9",
                "project": {"name": "fixture", "version": "0.2.9"},
                "operation_meta": {"last_updated": "2026-07-07"},
                "design_invariants": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    results = mica_core.run_pct_checks(tmp_path)
    assert mica_core.is_closed_contract(results)
    assert any(pid == "PCT-004" and status == "PASS" for pid, status, _ in results)

    yd, archive_path, playbook_path = mica_runtime.resolve_paths(tmp_path, tmp_path / "mica.yaml")
    assert yd["mode"] == "memory_first"
    assert archive_path == memory_dir / "mica_archive.json"
    assert playbook_path == memory_dir / "mica_playbook.md"


def test_memory_first_minimal_fixture_is_closed():
    fixture_root = REPO_ROOT / "fixtures" / "memory_first_minimal"

    results = mica_core.run_pct_checks(fixture_root)
    assert mica_core.is_closed_contract(results)
    assert any(pid == "PCT-004" and status == "PASS" for pid, status, _ in results)

    summary = mica_runtime.build_summary(fixture_root)
    assert summary["mode"] == "memory_first"
    assert summary["core_state"] == "CLOSED"

def test_memory_first_summary_reports_invoked_and_deferred_surfaces():
    fixture_root = REPO_ROOT / "fixtures" / "memory_first_minimal"

    summary = mica_runtime.build_summary(fixture_root)

    assert summary["invocation_contract"] == "memory_first"
    assert summary["loaded_surfaces"] == ["observations", "slots", "archive", "playbook"]
    assert summary["agent_context_surfaces"] == ["archive", "playbook", "slots"]
    assert {"sessions", "memories", "recall", "graph"}.issubset(set(summary["deferred_surfaces"]))


def test_memory_first_explicit_agent_context_surfaces_override_default(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (tmp_path / "mica.yaml").write_text(
        dedent(
            """
            mica_spec: "0.2.9"
            mode: memory_first
            invocation_protocol:
              primary_pattern: explicit
              agent_context_surfaces:
                - archive
                - playbook
            layers:
              - id: sessions
                kind: sessions
                path: memory/mica.sessions.jsonl
                loading_hint: on_demand
              - id: observe
                kind: observations
                path: memory/mica.observe.jsonl
                loading_hint: always
              - id: slots
                kind: slots
                path: memory/mica.slots.json
                loading_hint: always
              - id: archive_export
                kind: archive
                path: memory/mica_archive.json
                loading_hint: always
              - id: playbook_export
                kind: playbook
                path: memory/mica_playbook.md
                loading_hint: always
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (memory_dir / "mica.sessions.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.observe.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.slots.json").write_text('{"schema_version":"mica.slots.v1","slots":[]}', encoding="utf-8")
    (memory_dir / "mica_playbook.md").write_text("# playbook\n", encoding="utf-8")
    (memory_dir / "mica_archive.json").write_text(
        json.dumps(
            {
                "mica_spec": "0.2.9",
                "project": {"name": "fixture", "version": "0.2.9"},
                "operation_meta": {"last_updated": "2026-07-08"},
                "design_invariants": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = mica_runtime.build_summary(tmp_path)
    pct007 = next((status, msg) for pid, status, msg in mica_core.run_pct_checks(tmp_path) if pid == "PCT-007")

    assert summary["loaded_surfaces"] == ["observations", "slots", "archive", "playbook"]
    assert summary["agent_context_surfaces"] == ["archive", "playbook"]
    assert pct007[0] == "PASS"


def test_write_invocation_trace_persists_invoked_state(tmp_path: Path):
    fixture_root = REPO_ROOT / "fixtures" / "memory_first_minimal"
    summary = mica_runtime.build_summary(fixture_root)
    trace_path = tmp_path / "mica.invocation.jsonl"

    written = mica_runtime.write_invocation_trace(fixture_root, summary, trace_path)

    assert written == trace_path
    records = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["schema_version"] == "mica.invocation.v1"
    assert records[0]["session_id"] == "sess_20260707_0001"
    assert records[0]["loaded_surfaces"] == ["observations", "slots", "archive", "playbook"]
    assert records[0]["agent_context_surfaces"] == ["archive", "playbook", "slots"]


def test_memory_first_invocation_contract_fails_when_slots_not_marked_session_start(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (tmp_path / "mica.yaml").write_text(
        dedent(
            """
            mica_spec: "0.2.9"
            mode: memory_first
            layers:
              - id: sessions
                kind: sessions
                path: memory/mica.sessions.jsonl
                loading_hint: on_demand
              - id: observe
                kind: observations
                path: memory/mica.observe.jsonl
                loading_hint: always
              - id: memories
                kind: memories
                path: memory/mica.memories.jsonl
                loading_hint: on_demand
              - id: slots
                kind: slots
                path: memory/mica.slots.json
                loading_hint: on_demand
              - id: archive_export
                kind: archive
                path: memory/mica_archive.json
                loading_hint: always
              - id: playbook_export
                kind: playbook
                path: memory/mica_playbook.md
                loading_hint: always
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (memory_dir / "mica.sessions.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.observe.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.memories.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.slots.json").write_text('{"schema_version":"mica.slots.v1","slots":[]}', encoding="utf-8")
    (memory_dir / "mica_playbook.md").write_text("# playbook\n", encoding="utf-8")
    (memory_dir / "mica_archive.json").write_text(
        json.dumps(
            {
                "mica_spec": "0.2.9",
                "project": {"name": "fixture", "version": "0.2.9"},
                "operation_meta": {"last_updated": "2026-07-08"},
                "design_invariants": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    results = mica_core.run_pct_checks(tmp_path)
    pct007 = next((status, msg) for pid, status, msg in results if pid == "PCT-007")

    assert pct007[0] == "FAIL"
    assert "missing required session-start surfaces" in pct007[1]
    assert "slots" in pct007[1]

def test_memory_first_invocation_contract_fails_when_agent_context_surface_not_session_start_invoked(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (tmp_path / "mica.yaml").write_text(
        dedent(
            """
            mica_spec: "0.2.9"
            mode: memory_first
            invocation_protocol:
              primary_pattern: explicit
              agent_context_surfaces:
                - archive
                - memories
            layers:
              - id: observe
                kind: observations
                path: memory/mica.observe.jsonl
                loading_hint: always
              - id: memories
                kind: memories
                path: memory/mica.memories.jsonl
                loading_hint: on_demand
              - id: slots
                kind: slots
                path: memory/mica.slots.json
                loading_hint: always
              - id: archive_export
                kind: archive
                path: memory/mica_archive.json
                loading_hint: always
              - id: playbook_export
                kind: playbook
                path: memory/mica_playbook.md
                loading_hint: always
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (memory_dir / "mica.observe.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.memories.jsonl").write_text("", encoding="utf-8")
    (memory_dir / "mica.slots.json").write_text('{"schema_version":"mica.slots.v1","slots":[]}', encoding="utf-8")
    (memory_dir / "mica_playbook.md").write_text("# playbook\n", encoding="utf-8")
    (memory_dir / "mica_archive.json").write_text(
        json.dumps(
            {
                "mica_spec": "0.2.9",
                "project": {"name": "fixture", "version": "0.2.9"},
                "operation_meta": {"last_updated": "2026-07-08"},
                "design_invariants": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    pct007 = next((status, msg) for pid, status, msg in mica_core.run_pct_checks(tmp_path) if pid == "PCT-007")

    assert pct007[0] == "FAIL"
    assert "agent_context surfaces not session-start invoked" in pct007[1]
    assert "memories" in pct007[1]

def test_pct018_warns_when_agent_context_recall_lacks_invocation_trace(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (tmp_path / "mica.yaml").write_text(
        dedent(
            """
            mica_spec: "0.2.9"
            mode: memory_first
            flow_policy:
              enabled: true
            recall_policy:
              enabled: true
              inject_unapproved_candidates: false
            layers:
              - id: observe
                kind: observations
                path: memory/mica.observe.jsonl
                loading_hint: always
              - id: recall
                kind: recall
                path: memory/mica.recall.jsonl
                loading_hint: on_demand
              - id: candidates
                kind: candidates
                path: memory/mica.candidates.json
                loading_hint: on_demand
              - id: slots
                kind: slots
                path: memory/mica.slots.json
                loading_hint: always
              - id: archive_export
                kind: archive
                path: memory/mica_archive.json
                loading_hint: always
              - id: playbook_export
                kind: playbook
                path: memory/mica_playbook.md
                loading_hint: always
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (memory_dir / "mica.observe.jsonl").write_text(
        '{"schema_version":"mica.observe.v1","event_id":"obs_001","timestamp_utc":"2026-07-08T00:00:00Z","session_id":"sess_001","hook":"post_tool_use","scope":{"project":"fixture"},"summary":"obs","redaction":{"applied":false},"trust_tier":"native","source_system":"codex","event_hash":"sha256:111"}\n',
        encoding="utf-8",
    )
    (memory_dir / "mica.recall.jsonl").write_text(
        '{"schema_version":"mica.recall.v1","recall_id":"rec_001","timestamp_utc":"2026-07-08T00:01:00Z","session_id":"sess_001","candidate_id":"cand_001","source_event_ids":["obs_001"],"target":"agent_context","reason":"approved recall"}\n',
        encoding="utf-8",
    )
    (memory_dir / "mica.candidates.json").write_text(
        json.dumps(
            {
                "schema_version": "mica.candidates.v1",
                "candidates": [
                    {
                        "candidate_id": "cand_001",
                        "source_event_ids": ["obs_001"],
                        "status": "approved",
                        "operator_review": {
                            "state": "approved",
                            "reviewed_by": "op",
                            "reviewed_at_utc": "2026-07-08T00:00:30Z",
                            "decision_reason": "ok",
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (memory_dir / "mica.slots.json").write_text('{"schema_version":"mica.slots.v1","slots":[]}', encoding="utf-8")
    (memory_dir / "mica_playbook.md").write_text("# playbook\n", encoding="utf-8")
    (memory_dir / "mica_archive.json").write_text(
        json.dumps(
            {
                "mica_spec": "0.2.9",
                "project": {"name": "fixture", "version": "0.2.9"},
                "operation_meta": {"last_updated": "2026-07-08"},
                "design_invariants": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    pct018 = next((status, msg) for pid, status, msg in mica_core.run_pct_checks(tmp_path) if pid == "PCT-018")

    assert pct018[0] == "WARN"
    assert "target=agent_context but mica.invocation.jsonl absent" in pct018[1]


def test_pct018_passes_when_agent_context_recall_joins_invocation_trace(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (tmp_path / "mica.yaml").write_text(
        dedent(
            """
            mica_spec: "0.2.9"
            mode: memory_first
            flow_policy:
              enabled: true
            recall_policy:
              enabled: true
              inject_unapproved_candidates: false
            layers:
              - id: observe
                kind: observations
                path: memory/mica.observe.jsonl
                loading_hint: always
              - id: recall
                kind: recall
                path: memory/mica.recall.jsonl
                loading_hint: on_demand
              - id: candidates
                kind: candidates
                path: memory/mica.candidates.json
                loading_hint: on_demand
              - id: slots
                kind: slots
                path: memory/mica.slots.json
                loading_hint: always
              - id: archive_export
                kind: archive
                path: memory/mica_archive.json
                loading_hint: always
              - id: playbook_export
                kind: playbook
                path: memory/mica_playbook.md
                loading_hint: always
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (memory_dir / "mica.observe.jsonl").write_text(
        '{"schema_version":"mica.observe.v1","event_id":"obs_001","timestamp_utc":"2026-07-08T00:00:00Z","session_id":"sess_001","hook":"post_tool_use","scope":{"project":"fixture"},"summary":"obs","redaction":{"applied":false},"trust_tier":"native","source_system":"codex","event_hash":"sha256:111"}\n',
        encoding="utf-8",
    )
    (memory_dir / "mica.recall.jsonl").write_text(
        '{"schema_version":"mica.recall.v1","recall_id":"rec_001","timestamp_utc":"2026-07-08T00:01:00Z","session_id":"sess_001","candidate_id":"cand_001","source_event_ids":["obs_001"],"target":"agent_context","reason":"approved recall"}\n',
        encoding="utf-8",
    )
    (memory_dir / "mica.candidates.json").write_text(
        json.dumps(
            {
                "schema_version": "mica.candidates.v1",
                "candidates": [
                    {
                        "candidate_id": "cand_001",
                        "source_event_ids": ["obs_001"],
                        "status": "approved",
                        "operator_review": {
                            "state": "approved",
                            "reviewed_by": "op",
                            "reviewed_at_utc": "2026-07-08T00:00:30Z",
                            "decision_reason": "ok",
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (memory_dir / "mica.invocation.jsonl").write_text(
        '{"schema_version":"mica.invocation.v1","invocation_id":"inv_001","timestamp_utc":"2026-07-08T00:01:05Z","session_id":"sess_001","loaded_surfaces":["observations","archive","playbook","slots"],"agent_context_surfaces":["archive","playbook","slots"]}\n',
        encoding="utf-8",
    )
    (memory_dir / "mica.slots.json").write_text('{"schema_version":"mica.slots.v1","slots":[]}', encoding="utf-8")
    (memory_dir / "mica_playbook.md").write_text("# playbook\n", encoding="utf-8")
    (memory_dir / "mica_archive.json").write_text(
        json.dumps(
            {
                "mica_spec": "0.2.9",
                "project": {"name": "fixture", "version": "0.2.9"},
                "operation_meta": {"last_updated": "2026-07-08"},
                "design_invariants": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    pct018 = next((status, msg) for pid, status, msg in mica_core.run_pct_checks(tmp_path) if pid == "PCT-018")

    assert pct018[0] == "PASS"
    assert "joins cleanly with candidates, observations, and invocation trace" in pct018[1]

