"""Selection: which memory a session receives.

Before memory profiles, this was two hardcoded lists keyed on `mode`. Every
session got the same surfaces regardless of what it was for, while ~580 lines
existed to prove that whatever loaded had loaded. These tests cover the other
half of invocation.
"""

from __future__ import annotations

import json
import shutil
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
    assert summary["declared_profiles"] == ["default", "incident", "review"]


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


# --- playbook sections -------------------------------------------------------


def test_markdown_sections_are_parsed():
    preamble, sections = mica_core.parse_markdown_sections(
        "# Title\n\nintro\n\n## A\n\nbody a\n\n## B\n\nbody b\n"
    )

    assert "intro" in preamble
    assert sorted(sections) == ["A", "B"]
    assert "body a" in sections["A"]
    assert "body b" not in sections["A"]


def test_selection_keeps_the_preamble_and_drops_unselected_sections():
    text = "# Title\n\nframing\n\n## A\n\nbody a\n\n## B\n\nbody b\n"

    delivered, missing = mica_core.select_markdown_sections(text, ["B"])

    assert not missing
    assert "framing" in delivered
    assert "body b" in delivered
    assert "body a" not in delivered


def test_selection_reports_missing_sections():
    _, missing = mica_core.select_markdown_sections("# T\n\n## A\n\nx\n", ["A", "Nope"])

    assert missing == ["Nope"]


def _playbook_evidence(profile: str | None) -> dict:
    summary = mica_runtime.build_summary(FIXTURE, profile)
    return next(e for e in summary["surface_evidence"] if e["role"] == "playbook")


def test_sectioned_delivery_is_smaller_than_the_whole_file():
    whole = _playbook_evidence(None)
    sliced = _playbook_evidence("incident")

    assert "sections" not in whole
    assert sliced["sections"] == ["Incident Runbook"]
    assert sliced["bytes"] < whole["bytes"]


def test_evidence_digest_covers_the_slice_not_the_file():
    """Hashing the file while delivering part of it would misdescribe context."""
    sliced = _playbook_evidence("review")
    on_disk = mica_core.hash_surface_bytes(FIXTURE / "memory" / "mica_playbook.md")

    delivered, _ = mica_core.select_markdown_sections(
        (FIXTURE / "memory" / "mica_playbook.md").read_text(encoding="utf-8"),
        ["Review", "Invariants"],
    )
    expected = mica_core.hash_bytes(delivered.encode("utf-8"))

    assert (sliced["sha256"], sliced["bytes"]) == expected
    assert sliced["sha256"] != on_disk[0]


# --- drift is scoped to what was delivered -----------------------------------


def _seed_sectioned(tmp_path: Path) -> Path:
    project_root = tmp_path / "pkg"
    shutil.copytree(FIXTURE, project_root)
    mica_runtime.write_invocation_trace(
        project_root,
        mica_runtime.build_summary(project_root, "review"),
        project_root / "memory" / "mica.invocation.jsonl",
    )
    return project_root


def _ivc005(project_root: Path) -> tuple[str, str]:
    results = mica_core.run_invocation_trace_checks(project_root)
    return next((status, msg) for pid, status, msg in results if pid == "IVC-005")


def test_sectioned_capsule_can_be_written_without_false_drift(tmp_path: Path):
    """The write-time re-resolve must compare the slice, not the whole file."""
    project_root = _seed_sectioned(tmp_path)

    assert _ivc005(project_root)[0] == "PASS"


def test_editing_an_undelivered_section_is_not_drift(tmp_path: Path):
    project_root = _seed_sectioned(tmp_path)
    playbook = project_root / "memory" / "mica_playbook.md"
    playbook.write_text(
        playbook.read_text(encoding="utf-8").replace("Ask before", "EDITED. Ask before"),
        encoding="utf-8",
    )

    # 'Onboarding' was never delivered to this session, so it cannot have drifted.
    assert _ivc005(project_root)[0] == "PASS"


def test_editing_a_delivered_section_is_drift(tmp_path: Path):
    project_root = _seed_sectioned(tmp_path)
    playbook = project_root / "memory" / "mica_playbook.md"
    playbook.write_text(
        playbook.read_text(encoding="utf-8").replace(
            "Check the archive invariants", "EDITED. Check the archive invariants"
        ),
        encoding="utf-8",
    )

    status, msg = _ivc005(project_root)

    assert status == "WARN"
    assert "playbook" in msg


def test_removing_a_delivered_section_is_reported(tmp_path: Path):
    project_root = _seed_sectioned(tmp_path)
    playbook = project_root / "memory" / "mica_playbook.md"
    text = playbook.read_text(encoding="utf-8")
    start = text.index("## Invariants")
    end = text.index("## Onboarding")
    playbook.write_text(text[:start] + text[end:], encoding="utf-8")

    status, msg = _ivc005(project_root)

    assert status == "WARN"
    assert "sections removed" in msg


# --- contract enforcement for sections ---------------------------------------


def test_requesting_a_section_that_does_not_exist_fails_the_contract(tmp_path: Path):
    project_root = tmp_path / "pkg"
    shutil.copytree(FIXTURE, project_root)
    yaml_path = project_root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace(
            "        playbook: [Incident Runbook]", "        playbook: [Nonexistent Section]"
        ),
        encoding="utf-8",
    )

    status, msg = _pct007(project_root, "incident")

    assert status == "FAIL"
    assert "Nonexistent Section" in msg
    assert "available" in msg


def test_selecting_sections_of_an_uninvoked_surface_fails_the_contract(tmp_path: Path):
    project_root = tmp_path / "pkg"
    shutil.copytree(FIXTURE, project_root)
    yaml_path = project_root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace(
            "      surfaces: [archive, playbook]\n      sections:\n        playbook: [Incident Runbook]",
            "      surfaces: [archive]\n      sections:\n        playbook: [Incident Runbook]",
        ),
        encoding="utf-8",
    )

    status, msg = _pct007(project_root, "incident")

    assert status == "FAIL"
    assert "does not invoke" in msg
