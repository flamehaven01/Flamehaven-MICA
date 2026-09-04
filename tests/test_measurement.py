"""Measurement, and the version-comparison defect it surfaced.

MICA had no metrics. Building one exposed that PCT-006 was stating a number it
could not support: with versions packed as major*10000 + minor*100 + patch, a
package declaring 0.1.9 was reported as "99 version(s) behind" canonical 0.2.8.
Across a minor boundary that difference counts nothing. One of the six live
consumer packages declares 0.1.9, so the false number was being shipped.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core  # noqa: E402
import mica_measure  # noqa: E402

# --- PCT-006 answers "do these tools define this contract" -------------------


def _compat(spec: str) -> tuple[str, str] | None:
    """(status, message) for a declared contract, or None when it is supported."""
    results = mica_core._spec_compatibility_result(spec)
    return (results[0][1], results[0][2]) if results else None


@pytest.mark.parametrize("spec", mica_core.SUPPORTED_CONTRACT_VERSIONS)
def test_a_supported_contract_is_silent(spec: str):
    """A package on a contract these tools define has nothing to report."""
    assert _compat(spec) is None


def test_the_current_contract_is_one_of_the_supported_ones():
    assert mica_core.MICA_CONTRACT_VERSION in mica_core.SUPPORTED_CONTRACT_VERSIONS


def test_the_tool_version_is_not_the_contract_version():
    """Conflating them is what made every 0.2.x consumer read as behind the
    moment the tools reached 3.x, while nothing about those packages changed."""
    assert mica_core.MICA_TOOL_VERSION != mica_core.MICA_CONTRACT_VERSION
    assert mica_core.MICA_TOOL_VERSION not in mica_core.SUPPORTED_CONTRACT_VERSIONS


@pytest.mark.parametrize("spec", mica_core.LEGACY_RESOLVABLE_CONTRACTS)
def test_a_legacy_contract_is_informational_not_a_warning(spec: str):
    """These tools read it. That is a different statement from supporting it,
    and neither one is a defect in the package."""
    status, message = _compat(spec)

    assert status == "INFO"
    assert "legacy-resolvable" in message
    assert "full contract support is not claimed" in message


@pytest.mark.parametrize("spec", ["0.2.10", "0.3.0", "3.0.0", "3.0.1", "9.9.9"])
def test_an_undefined_contract_warns_without_claiming_to_support_it(spec: str):
    """An open upper bound would have called 0.2.10 and every future 3.x
    supported. None of those contracts is designed, so claiming them would be a
    false statement about what these tools understand."""
    status, message = _compat(spec)

    assert status == "WARN"
    assert "not a contract version these tools define" in message
    assert "Supported:" in message


def test_the_tools_own_release_number_is_not_a_supported_contract():
    """3.0.1 is a tool release. A package declaring it has declared a contract
    that does not exist."""
    status, _ = _compat(mica_core.MICA_TOOL_VERSION)

    assert status == "WARN"


def test_a_malformed_version_is_reported_rather_than_matched():
    status, message = _compat("not-a-version")

    assert status == "WARN"
    assert "not a version number" in message


def test_no_verdict_measures_distance_or_prescribes_an_upgrade():
    """The old check reported how far a package was from the tool version and
    suggested closing the gap. Distance is not the question a maintainer has,
    and MICA does not push consumers toward one version: each package carries
    its own memory in its own form and evolves on its own track."""
    forbidden = (
        "behind",
        "ahead",
        "consider upgrading",
        "should upgrade",
        "must upgrade",
        "version(s)",
        "canonical",
    )

    for spec in ("0.1.9", "0.2.10", "3.0.0", "not-a-version", "0.0.1"):
        result = _compat(spec)
        if result is None:
            continue
        for phrase in forbidden:
            assert phrase not in result[1].lower(), (spec, phrase, result[1])


def test_every_supported_contract_is_a_real_version_number():
    import re as _re

    for spec in (*mica_core.SUPPORTED_CONTRACT_VERSIONS, *mica_core.LEGACY_RESOLVABLE_CONTRACTS):
        assert _re.fullmatch(r"\d+\.\d+\.\d+", spec), spec


def test_supported_and_legacy_contracts_do_not_overlap():
    """A contract is either fully supported or read on sufferance, not both."""
    assert not set(mica_core.SUPPORTED_CONTRACT_VERSIONS) & set(
        mica_core.LEGACY_RESOLVABLE_CONTRACTS
    )


# --- the measurement itself --------------------------------------------------


def test_measure_reports_context_budget():
    row = mica_measure.measure(FIXTURES_DIR / "memory_profiles")

    assert row["context_budget"]["agent_context_bytes"] > 0
    assert row["axes"]["contract"] == "CLOSED"
    assert row["declared_profiles"] == ["default", "incident", "review"]


def test_profiles_change_the_measured_context_budget():
    """The point of P1/P2: a session's memory is not one fixed size."""
    default = mica_measure.measure(FIXTURES_DIR / "memory_profiles", "default")
    incident = mica_measure.measure(FIXTURES_DIR / "memory_profiles", "incident")

    assert (
        incident["context_budget"]["agent_context_bytes"]
        < (default["context_budget"]["agent_context_bytes"])
    )
    assert incident["context_budget"]["sectioned_surfaces"] == 1
    assert default["context_budget"]["sectioned_surfaces"] == 0


def test_capsule_coverage_identifies_exact_bytes():
    row = mica_measure.measure(FIXTURES_DIR / "invocation_capsule_v2")

    assert row["capsule_coverage"]["identifies_exact_bytes"]
    assert row["capsule_coverage"]["surfaces_with_digest"] == row["surfaces"]["invoked"]


def test_measure_does_not_recompute_the_version_comparison():
    """Two implementations of one comparison is the drift MICA exists to catch."""
    source = (TOOLS_DIR / "mica_measure.py").read_text(encoding="utf-8")

    assert "_parse_version" not in source
    assert "_spec_notes" in source


def test_measure_surfaces_the_pct006_message_verbatim():
    """This used to filter the check's output on the substring "canonical", the
    same filter the tool carried. Once v3.0.2 reworded PCT-006 both sides went
    empty and the test asserted nothing while still passing."""
    import contextlib
    import io

    package = FIXTURES_DIR / "valid_bound_di"
    with contextlib.redirect_stdout(io.StringIO()):
        results = mica_core.run_pct_checks(package)
    warnings = [msg for pid, status, msg in results if pid == "PCT-006" and status == "WARN"]

    assert mica_measure.measure(package)["spec_notes"] == warnings


def test_cli_emits_json():
    proc = subprocess.run(
        [
            sys.executable,
            str(TOOLS_DIR / "mica_measure.py"),
            str(FIXTURES_DIR / "memory_profiles"),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    rows = json.loads(proc.stdout)
    assert len(rows) == 1
    assert rows[0]["package"] == "memory-profiles"


def test_the_supported_floor_is_pinned_by_a_fixture():
    """The floor was decided from live consumer packages, none of which live in
    this repository. An external package can change or disappear, so the
    boundary this project publishes is pinned in-repo instead."""
    import contextlib
    import io

    floor = min(mica_core.SUPPORTED_CONTRACT_VERSIONS, key=mica_core._parse_version)
    fixture = Path(__file__).resolve().parent.parent / "fixtures" / "contract_floor"

    declared = mica_core.load_yaml(fixture / "mica.yaml")["mica_spec"]
    assert declared == floor, f"the floor fixture declares {declared}, the floor is {floor}"

    with contextlib.redirect_stdout(io.StringIO()):
        results = mica_core.run_pct_checks(fixture)
    pct006 = [(status, message) for check, status, message in results if check == "PCT-006"]

    assert pct006 == [("PASS", f"mica_spec aligned: {floor}")], pct006
    assert mica_core.evaluate_axes(results)["contract"] == "CLOSED"


# --- the instrument agrees with the check it reports on ----------------------


def _measured_spec_notes(tmp_path: Path, spec: str) -> list[str]:
    """Build a package at `spec` and read what mica_measure records for it."""
    import shutil

    import mica_measure

    root = tmp_path / "pkg"
    shutil.copytree(Path(__file__).resolve().parent.parent / "fixtures" / "contract_floor", root)
    for relative in ("mica.yaml", "memory/mica_archive.json"):
        path = root / relative
        path.write_text(path.read_text(encoding="utf-8").replace("0.2.4", spec), encoding="utf-8")
    return mica_measure.measure(root, None)["spec_notes"]


def _pct006_warnings(tmp_path_root: Path) -> list[str]:
    import contextlib
    import io

    with contextlib.redirect_stdout(io.StringIO()):
        results = mica_core.run_pct_checks(tmp_path_root)
    return [m for c, s, m in results if c == "PCT-006" and s == "WARN"]


@pytest.mark.parametrize("spec", ["0.2.4", "0.2.9"])
def test_a_supported_contract_records_no_note(tmp_path: Path, spec: str):
    assert _measured_spec_notes(tmp_path, spec) == []


def test_a_legacy_contract_records_no_warning_because_it_is_informational(tmp_path: Path):
    """0.1.9 is reported as INFO, not WARN. The measurement carries warnings."""
    assert _measured_spec_notes(tmp_path, "0.1.9") == []


def test_an_unknown_contract_is_carried_into_the_measurement(tmp_path: Path):
    """The filter matched on the substring "canonical", so when v3.0.2 rewrote
    PCT-006 around supported contracts the word vanished and a package the check
    warned about recorded `spec_note: null`. The instrument disagreed with the
    check it reports on."""
    notes = _measured_spec_notes(tmp_path, "0.2.10")

    assert len(notes) == 1
    assert "not a contract version these tools define" in notes[0]


def test_a_yaml_archive_mismatch_is_carried_too(tmp_path: Path):
    """A different PCT-006 warning, and one whose wording never mentioned
    contracts or canonical. Both must reach the measurement."""
    import shutil

    import mica_measure

    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "contract_floor", root)
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace('mica_spec: "0.2.4"', 'mica_spec: "0.2.9"'),
        encoding="utf-8",
    )

    note = mica_measure.measure(root, None)["spec_note"]

    assert note is not None
    assert "drift" in note


def test_the_measurement_note_is_exactly_what_the_check_said(tmp_path: Path):
    """No paraphrase and no second opinion: two implementations of one
    comparison is the drift this project exists to catch."""
    import shutil

    import mica_measure

    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "contract_floor", root)
    for relative in ("mica.yaml", "memory/mica_archive.json"):
        path = root / relative
        path.write_text(
            path.read_text(encoding="utf-8").replace("0.2.4", "9.9.9"), encoding="utf-8"
        )

    assert mica_measure.measure(root, None)["spec_notes"] == _pct006_warnings(root)


def test_two_warnings_in_one_run_are_both_recorded(tmp_path: Path):
    """PCT-006 warns twice when a package both disagrees with its own archive
    and declares a contract these tools do not define. Returning the first note
    dropped the second, so a package with both recorded only the drift and the
    unknown contract vanished from the measurement."""
    import shutil

    import mica_measure

    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "contract_floor", root)
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace('mica_spec: "0.2.4"', 'mica_spec: "0.2.10"'),
        encoding="utf-8",
    )
    archive = root / "memory" / "mica_archive.json"
    archive.write_text(
        archive.read_text(encoding="utf-8").replace('"0.2.4"', '"0.2.9"'), encoding="utf-8"
    )

    notes = mica_measure.measure(root, None)["spec_notes"]

    assert len(notes) == 2
    assert notes == _pct006_warnings(root), "character and order must match the check"
    assert any("drift" in note for note in notes)
    assert any("not a contract version" in note for note in notes)


def test_the_singular_field_is_the_first_note_and_can_hide_one(tmp_path: Path):
    """`spec_note` is kept for readers written against it. This records what it
    costs: with two warnings it shows one, which is why `spec_notes` is the
    canonical field."""
    import shutil

    import mica_measure

    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "contract_floor", root)
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace('mica_spec: "0.2.4"', 'mica_spec: "0.2.10"'),
        encoding="utf-8",
    )
    archive = root / "memory" / "mica_archive.json"
    archive.write_text(
        archive.read_text(encoding="utf-8").replace('"0.2.4"', '"0.2.9"'), encoding="utf-8"
    )

    row = mica_measure.measure(root, None)

    assert row["spec_note"] == row["spec_notes"][0]
    assert len(row["spec_notes"]) > 1
