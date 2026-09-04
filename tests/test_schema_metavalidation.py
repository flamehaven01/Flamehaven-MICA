"""Every shipped JSON Schema must itself be a valid schema.

The repository ships schemas as a portable contract for external consumers.
Nothing validated the schemas themselves, so an invalid regex could ship while
the hand-rolled Python checks still passed.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# Root-level schemas are the shipped package contract. The rglob also reaches
# schemas under experiments/, because a schema that does not parse is broken
# wherever it lives, and the metavalidation costs nothing per file.
SHIPPED_SCHEMA_FILES = sorted(REPO_ROOT.glob("*.schema.json"))
# `.claude` holds agent worktrees and `Legacy` holds untracked history; both are
# gitignored and absent on CI, so including them would make the collected test
# count differ between a developer machine and the runner.
_UNTRACKED_TREES = {".git", ".claude", "Legacy"}
SCHEMA_FILES = sorted(
    path for path in REPO_ROOT.rglob("*.schema.json") if _UNTRACKED_TREES.isdisjoint(path.parts)
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_files_are_discovered():
    assert SHIPPED_SCHEMA_FILES, "expected shipped *.schema.json files at the repository root"
    assert len(SCHEMA_FILES) >= len(SHIPPED_SCHEMA_FILES)


@pytest.mark.parametrize("schema_path", SCHEMA_FILES, ids=lambda p: p.name)
def test_schema_passes_metavalidation(schema_path: Path):
    schema = _load(schema_path)
    validator = jsonschema.validators.validator_for(schema)
    validator.check_schema(schema)


# --- invocation schema contract ---------------------------------------------


@pytest.fixture(scope="module")
def invocation_validator():
    schema = _load(REPO_ROOT / "mica.invocation.schema.json")
    return jsonschema.validators.validator_for(schema)(schema)


def _record(**overrides) -> dict:
    base = {
        "schema_version": "mica.invocation.v1",
        "invocation_id": "inv_1",
        "timestamp_utc": "2026-09-03T00:00:00Z",
        "project_root": "/x",
        "project": {"name": "n", "version": "1"},
        "package_state": "INVOCATION_MODE",
        "core_state": "CLOSED",
        "flow_state": None,
        "mode": "memory_injection",
        "pattern": "readme_protocol",
        "session_id": "s1",
        "invocation_contract": "archive_first",
        "loaded_surfaces": ["archive"],
        "agent_context_surfaces": ["archive"],
        "deferred_surfaces": [],
        "missing_invoked_surfaces": [],
        "active_critical_invariants": [],
        "last_updated": "2026-09-03",
    }
    base.update(overrides)
    return base


def _evidence(path: str = "memory/mica_archive.json") -> list[dict]:
    return [
        {
            "role": "archive",
            "path": path,
            "sha256": "sha256:" + "b" * 64,
            "bytes": 1,
            "audience": "agent_context",
            "delivery_state": "resolved",
        }
    ]


def _v2(**overrides) -> dict:
    defaults = {
        "schema_version": "mica.invocation.v2",
        "trigger": {"kind": "review", "ref": "git:abc"},
        "surface_evidence": _evidence(),
        "capsule_hash": "sha256:" + "a" * 64,
    }
    defaults.update(overrides)
    return _record(**defaults)


def test_v1_record_is_valid_without_continuity_fields(invocation_validator):
    assert invocation_validator.is_valid(_record())


def test_v2_record_requires_continuity_fields(invocation_validator):
    for missing in ("trigger", "surface_evidence", "capsule_hash"):
        record = _v2()
        del record[missing]
        assert not invocation_validator.is_valid(record), (
            f"v2 record without {missing} must be rejected by the schema"
        )


def test_v2_record_with_continuity_fields_is_valid(invocation_validator):
    assert invocation_validator.is_valid(_v2())


BACKSLASH = chr(92)


@pytest.mark.parametrize(
    "path, expected_valid",
    [
        ("memory/mica_archive.json", True),
        ("memory/sub/deep.json", True),
        (f"memory{BACKSLASH}mica_archive.json", False),
        (f"{BACKSLASH}{BACKSLASH}server{BACKSLASH}share.json", False),
        ("/abs/mica_archive.json", False),
        ("C:/mica_archive.json", False),
        ("../outside.json", False),
        ("memory/../../etc/passwd", False),
    ],
)
def test_surface_evidence_path_pattern(invocation_validator, path: str, expected_valid: bool):
    assert invocation_validator.is_valid(_v2(surface_evidence=_evidence(path))) is expected_valid


def test_delivery_state_vocabulary_is_closed(invocation_validator):
    """No state may imply comprehension."""
    for forbidden in ("read", "understood", "complied", "verified"):
        entry = _evidence()
        entry[0]["delivery_state"] = forbidden
        assert not invocation_validator.is_valid(_v2(surface_evidence=entry))


# --- real records must satisfy the shipped schema ----------------------------
#
# The hand-rolled Python checks and the shipped JSON Schema are two independent
# contracts. Nothing compared them, so the runtime emitted invocation_id values
# ("inv_<ISO>Z") that the schema's lowercase-only pattern rejected, and every
# committed fixture trace was invalid against the schema it ships with.


def _runtime_record(trigger=None):
    import sys

    tools_dir = REPO_ROOT / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import mica_runtime

    fixture = REPO_ROOT / "fixtures" / "invocation_capsule_v2"
    return mica_runtime.build_invocation_trace_record(
        mica_runtime.build_summary(fixture), trigger=trigger
    )


def test_runtime_generated_record_satisfies_the_shipped_schema(invocation_validator):
    record = _runtime_record(trigger={"kind": "review", "ref": "git:abc"})

    errors = sorted(invocation_validator.iter_errors(record), key=lambda e: list(e.path))

    assert not errors, [f"{list(e.path)}: {e.message}" for e in errors]


def test_runtime_record_without_a_trigger_is_valid(invocation_validator):
    """trigger is required for v2 but may be null when no lifecycle event applies."""
    record = _runtime_record()

    assert record["trigger"] is None
    assert invocation_validator.is_valid(record)


COMMITTED_TRACES = sorted((REPO_ROOT / "fixtures").rglob("mica.invocation.jsonl"))


def test_committed_traces_are_discovered():
    assert COMMITTED_TRACES, "expected committed invocation traces in fixtures/"


@pytest.mark.parametrize("trace_path", COMMITTED_TRACES, ids=lambda p: p.parent.parent.name)
def test_committed_trace_records_satisfy_the_shipped_schema(invocation_validator, trace_path: Path):
    for lineno, line in enumerate(trace_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        errors = sorted(invocation_validator.iter_errors(record), key=lambda e: list(e.path))
        assert not errors, f"{trace_path.name}:{lineno} -> " + "; ".join(
            f"{list(e.path)}: {e.message}" for e in errors
        )
