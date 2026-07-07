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
