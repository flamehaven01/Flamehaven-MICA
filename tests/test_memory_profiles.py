"""Selection: which memory a session receives.

Before memory profiles, this was two hardcoded lists keyed on `mode`. Every
session got the same surfaces regardless of what it was for, while ~580 lines
existed to prove that whatever loaded had loaded. These tests cover the other
half of invocation.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core  # noqa: E402
import mica_runtime  # noqa: E402

FIXTURE = FIXTURES_DIR / "memory_profiles"


def _pct007(project_root: Path, profile: str | None = None) -> tuple[str, str]:
    results = mica_core.run_pct_checks(project_root, profile)
    return next((status, msg) for pid, status, msg in results if pid == "PCT-007")


# --- selection ---------------------------------------------------------------


def test_profile_changes_which_surfaces_load():
    baseline = mica_runtime.build_summary(FIXTURE)
    review = mica_runtime.build_summary(FIXTURE, "review")

    assert baseline["loaded_surfaces"] == ["archive", "playbook"]
    assert review["loaded_surfaces"] == ["archive", "playbook", "lessons"]


def test_default_profile_applies_when_none_requested():
    summary = mica_runtime.build_summary(FIXTURE)

    assert summary["active_profile"] == "default"
    assert summary["declared_profiles"] == ["default", "review"]


def test_agent_context_follows_the_profile():
    review = mica_runtime.build_summary(FIXTURE, "review")

    assert "lessons" in review["agent_context_surfaces"]


def test_surfaces_outside_the_profile_are_deferred():
    baseline = mica_runtime.build_summary(FIXTURE)

    assert "lessons" in baseline["deferred_surfaces"]
    assert "lessons" not in baseline["loaded_surfaces"]


# --- backward compatibility --------------------------------------------------


@pytest.mark.parametrize(
    "fixture, expected",
    [
        ("valid_bound_di", ["archive", "playbook"]),
        ("memory_first_minimal", ["observations", "slots", "archive", "playbook"]),
    ],
)
def test_packages_without_profiles_resolve_exactly_as_before(fixture: str, expected: list[str]):
    """A package that declares no profiles must be untouched by this feature."""
    summary = mica_runtime.build_summary(FIXTURES_DIR / fixture)

    assert summary["loaded_surfaces"] == expected
    assert summary["active_profile"] is None
    assert summary["declared_profiles"] == []


def test_requesting_a_profile_on_a_package_without_profiles_fails_the_contract():
    status, msg = _pct007(FIXTURES_DIR / "valid_bound_di", "review")

    assert status == "FAIL"
    assert "not declared" in msg


# --- contract enforcement ----------------------------------------------------


def test_unknown_profile_breaks_the_invocation_contract():
    results = mica_core.run_pct_checks(FIXTURE, "does_not_exist")
    axes = mica_core.evaluate_axes(results)
    status, msg = _pct007(FIXTURE, "does_not_exist")

    assert status == "FAIL"
    assert "does_not_exist" in msg
    assert axes["contract"] == "INCOMPLETE"


def test_declared_profiles_are_listed_in_the_failure():
    _, msg = _pct007(FIXTURE, "does_not_exist")

    assert "default" in msg and "review" in msg


def test_profile_naming_an_undeclared_surface_fails_the_contract(tmp_path: Path):
    project_root = tmp_path / "pkg"
    (project_root / "memory").mkdir(parents=True)
    (project_root / "mica.yaml").write_text(
        "\n".join(
            [
                'mica_spec: "0.2.8"',
                "name: bad-profile",
                "mode: memory_injection",
                "layers:",
                "  - id: archive",
                "    kind: archive",
                "    path: memory/mica_archive.json",
                "  - id: playbook",
                "    kind: playbook",
                "    path: memory/mica_playbook.md",
                "invocation_protocol:",
                "  primary_pattern: readme_protocol",
                "  profiles:",
                "    review:",
                "      surfaces: [archive, playbook, runbook]",
            ]
        ),
        encoding="utf-8",
    )
    (project_root / "memory" / "mica_playbook.md").write_text("# playbook\n", encoding="utf-8")
    (project_root / "memory" / "mica_archive.json").write_text(
        json.dumps(
            {
                "mica_spec": "0.2.8",
                "project": {"name": "bad-profile", "version": "1.0.0"},
                "design_invariants": [],
                "operation_meta": {"last_updated": "2026-09-03"},
            }
        ),
        encoding="utf-8",
    )

    status, msg = _pct007(project_root, "review")

    assert status == "FAIL"
    assert "runbook" in msg


# --- evidence ----------------------------------------------------------------


def test_capsule_evidence_covers_exactly_the_profile_surfaces():
    for profile, expected in [
        (None, ["archive", "playbook"]),
        ("review", ["archive", "playbook", "lessons"]),
    ]:
        summary = mica_runtime.build_summary(FIXTURE, profile)
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "mica.invocation.jsonl"
            mica_runtime.write_invocation_trace(
                FIXTURE, summary, trace, trigger={"kind": "review", "ref": "git:abc"}
            )
            record = json.loads(trace.read_text(encoding="utf-8").strip())

        assert [entry["role"] for entry in record["surface_evidence"]] == expected


def test_trace_records_the_profile_that_selected_the_surfaces():
    summary = mica_runtime.build_summary(FIXTURE, "review")
    with tempfile.TemporaryDirectory() as tmp:
        trace = Path(tmp) / "mica.invocation.jsonl"
        mica_runtime.write_invocation_trace(FIXTURE, summary, trace)
        record = json.loads(trace.read_text(encoding="utf-8").strip())

    assert record["profile"] == "review"


def test_trace_profile_is_null_without_declared_profiles():
    fixture = FIXTURES_DIR / "invocation_capsule_v2"
    summary = mica_runtime.build_summary(fixture)
    record = mica_runtime.build_invocation_trace_record(summary)

    assert record["profile"] is None


def test_runtime_text_reports_the_active_profile():
    text = mica_runtime.emit_text(mica_runtime.build_summary(FIXTURE, "review"))

    assert "Profile   : review" in text
