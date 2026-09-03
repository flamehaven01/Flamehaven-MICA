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


# --- specialised surfaces ----------------------------------------------------


def _declared_profiles(package: Path) -> list[str]:
    import mica_primitives

    yd = mica_primitives.load_yaml(package / "mica.yaml") or {}
    inv = yd.get("invocation_protocol")
    profiles = inv.get("profiles") if isinstance(inv, dict) else None
    return sorted(profiles) if isinstance(profiles, dict) else []


def test_a_specialised_playbook_may_reach_the_agent():
    """A package that keeps several playbooks apart names them `playbook-eqa`,
    `playbook-bav`. Those are playbooks; the closed six-role vocabulary had no
    way to say so, so such a package could not deliver them at all."""
    assert mica_core._surface_family("playbook-eqa") == "playbook"
    assert mica_core._is_audience_eligible(
        "playbook-eqa", mica_core._AGENT_CONTEXT_ALLOWED_SURFACES
    )


def test_a_qualifier_cannot_move_a_surface_to_another_audience():
    """Narrowing a surface never changes who may receive it."""
    for role in ("sessions-2024", "observations-raw", "candidates-pending"):
        assert not mica_core._is_audience_eligible(role, mica_core._AGENT_CONTEXT_ALLOWED_SURFACES)
        assert mica_core._is_audience_eligible(role, mica_core._OPERATOR_ONLY_ALLOWED_SURFACES)


def test_an_unrelated_surface_is_still_rejected():
    assert not mica_core._is_audience_eligible(
        "credibility-architecture", mica_core._AGENT_CONTEXT_ALLOWED_SURFACES
    )


def test_a_specialised_playbook_reaches_agent_context_through_the_contract(
    tmp_path: Path,
):
    """The unit rule, exercised end to end: declare a domain playbook, select it
    with a profile, and it arrives in the agent context with the contract closed."""
    import mica_primitives

    root = tmp_path / "pkg"
    shutil.copytree(FIXTURE, root)
    (root / "memory" / "playbook-eqa.md").write_text(
        "## Evidence Quality\n\nDomain rules.\n", encoding="utf-8"
    )
    yaml_path = root / "mica.yaml"
    text = yaml_path.read_text(encoding="utf-8")
    text = text.replace(
        "invocation_protocol:",
        "  - name: playbook-eqa\n"
        "    path: memory/playbook-eqa.md\n"
        "    format: markdown\n"
        "    loading_hint: on_demand\n"
        "\n"
        "invocation_protocol:",
        1,
    )
    text = text.replace(
        "  profiles:",
        "  agent_context_surfaces: [archive, playbook, playbook-eqa]\n"
        "  profiles:\n"
        "    eqa:\n"
        "      surfaces: [archive, playbook, playbook-eqa]",
        1,
    )
    yaml_path.write_text(text, encoding="utf-8")

    status, _ = _pct007(root, "eqa")
    contract = mica_core.resolve_invocation_contract(mica_primitives.load_yaml(yaml_path), "eqa")

    assert status == "PASS"
    assert "playbook-eqa" in contract["agent_context_surfaces"]


# --- the ceiling is not a per-session manifest -------------------------------


def test_a_permitted_surface_another_profile_uses_is_deselected_not_missing():
    """`agent_context_surfaces` says what may reach the agent. The profile says
    what does. Before this distinction, declaring a surface that only one
    profile invoked failed the contract under every other profile."""
    contract = mica_core.resolve_invocation_contract(
        __import__("mica_primitives").load_yaml(FIXTURES_DIR / "handoff_surface" / "mica.yaml"),
        "default",
    )

    assert "handoff" in contract["deselected_agent_context_surfaces"]
    assert contract["non_invoked_agent_context_surfaces"] == []
    assert "handoff" not in contract["agent_context_surfaces"]


def test_without_profiles_an_uninvoked_permitted_surface_is_still_a_fault():
    """Nothing explains the gap when no profile did the selecting."""
    contract = mica_core.resolve_invocation_contract(
        {
            "mode": "archive_first",
            "layers": [
                {"name": "archive", "loading_hint": "always"},
                {"name": "playbook", "loading_hint": "always"},
                {"name": "handoff", "loading_hint": "on_demand"},
            ],
            "invocation_protocol": {
                "primary_pattern": "readme_protocol",
                "agent_context_surfaces": ["archive", "playbook", "handoff"],
            },
        }
    )

    assert contract["non_invoked_agent_context_surfaces"] == ["handoff"]
    assert contract["deselected_agent_context_surfaces"] == []


@pytest.mark.parametrize(
    "package",
    sorted(p for p in FIXTURES_DIR.iterdir() if (p / "mica.yaml").exists()),
    ids=lambda p: p.name,
)
def test_a_package_closes_its_contract_under_all_profiles_or_none(package: Path):
    """The guard that was missing.

    The handoff fixture shipped closing its contract under `resume` and failing
    under `default` and under no profile at all. No test looked: one asserted
    `resume`, the rest went through `build_summary`, which never evaluates the
    contract.

    Checking that a closing package stays closed would not have caught it --
    that fixture did not close without a profile, so it would have been skipped.
    The invariant is that profiles do not decide whether the contract holds.
    A negative fixture closes under nothing and passes here unremarked.
    """
    profiles = _declared_profiles(package)
    verdicts = {
        profile: mica_core.evaluate_axes(mica_core.run_pct_checks(package, profile))["contract"]
        for profile in [None, *profiles]
    }

    assert len(set(verdicts.values())) == 1, f"{package.name}: {verdicts}"
