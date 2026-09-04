"""Counterexamples from an adversarial audit of the v3.0.0 Origin milestone.

Every test here failed before the fix. They are kept so the same class of
overclaim cannot return: a contract that says more than it verified, evidence
that can be forged, a surface path that resolves to something unreadable, a
profile that silently degrades, and a measurement that reports coverage it
does not have.
"""

from __future__ import annotations

import json
import shutil
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
import mica_evidence  # noqa: E402
import mica_measure  # noqa: E402
import mica_primitives  # noqa: E402
import mica_runtime  # noqa: E402

FENCE = chr(96) * 3


def _run_pct(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOLS_DIR / "mica_pct.py"), *args],
        capture_output=True,
        text=True,
    )


def _status(results, check_id):
    return [status for pid, status, _ in results if pid == check_id]


def _message(results, check_id):
    return next(msg for pid, _, msg in results if pid == check_id)


# --- P0-1: the contract must not claim delivery it did not verify ------------


def test_pct009_does_not_claim_surfaces_reached_the_session():
    """Resolution is not delivery. The old message said 'reached'."""
    results = mica_core.run_pct_checks(FIXTURES_DIR / "valid_bound_di")
    message = next(msg for pid, status, msg in results if pid == "PCT-009" and status == "PASS")

    assert "resolved" in message
    assert "reached the session" not in message


def test_invalid_recorded_trace_fails_the_run(tmp_path: Path):
    """A corrupted capsule reported IVC-004 FAIL and still exited 0."""
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "invocation_capsule_v2", root)
    trace = root / "memory" / "mica.invocation.jsonl"
    record = json.loads(trace.read_text(encoding="utf-8").strip())
    record["agent_context_surfaces"] = ["archive", "playbook", "ghost"]
    trace.write_text(json.dumps(record) + "\n", encoding="utf-8")

    proc = _run_pct(str(root))

    assert "IVC-004 [FAIL" in proc.stdout
    assert proc.returncode == 1
    assert "invocation_trace" in proc.stdout


# --- P0-2: the profile decides which memory was selected, so bind it ---------


def test_profile_is_covered_by_the_capsule_hash():
    assert "profile" in mica_evidence._CAPSULE_HASH_FIELDS


def test_forging_the_profile_changes_the_capsule_hash():
    record = mica_runtime.build_invocation_trace_record(
        mica_runtime.build_summary(FIXTURES_DIR / "invocation_capsule_v2")
    )
    original = record["capsule_hash"]
    record["profile"] = "forged_profile"

    assert mica_evidence.compute_capsule_hash(record) != original


def test_forged_profile_is_caught_by_the_validator(tmp_path: Path):
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "invocation_capsule_v2", root)
    trace = root / "memory" / "mica.invocation.jsonl"
    record = json.loads(trace.read_text(encoding="utf-8").strip())
    record["profile"] = "forged_profile"
    trace.write_text(json.dumps(record) + "\n", encoding="utf-8")

    results = mica_core.run_invocation_trace_checks(root)

    assert _status(results, "IVC-004") == ["FAIL"]


# --- P0-3: a declared surface must be a readable file inside the root --------


def test_directory_at_a_surface_path_fails_the_contract(tmp_path: Path):
    """A directory passed PCT-003 while producing no evidence for that role."""
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "memory_profiles", root)
    playbook = root / "memory" / "mica_playbook.md"
    playbook.unlink()
    playbook.mkdir()

    results = mica_core.run_pct_checks(root)

    assert _status(results, "PCT-003") == ["FAIL"]
    assert mica_core.evaluate_axes(results)["contract"] == "INCOMPLETE"


def test_surface_path_escaping_the_root_fails_the_contract(tmp_path: Path):
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "memory_profiles", root)
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace(
            "    path: memory/mica_playbook.md", "    path: ../outside.md"
        ),
        encoding="utf-8",
    )
    (tmp_path / "outside.md").write_text("# outside\n", encoding="utf-8")

    results = mica_core.run_pct_checks(root)

    assert _status(results, "PCT-003") == ["FAIL"]


# --- P1-4: a malformed profile must fail, not degrade quietly ----------------


def _profile_pkg(tmp_path: Path, surfaces: str) -> Path:
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "memory_profiles", root)
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace(
            "      surfaces: [archive, playbook, lessons]", f"      surfaces: {surfaces}"
        ),
        encoding="utf-8",
    )
    return root


def test_profile_with_no_usable_surfaces_fails(tmp_path: Path):
    """An empty list silently fell back to the mode defaults."""
    results = mica_core.run_pct_checks(_profile_pkg(tmp_path, "[]"), "review")

    assert _status(results, "PCT-007") == ["FAIL"]
    assert "no usable surfaces" in _message(results, "PCT-007")


def test_profile_repeating_a_surface_fails(tmp_path: Path):
    """Duplicates produced duplicate loaded surfaces and duplicate evidence."""
    results = mica_core.run_pct_checks(_profile_pkg(tmp_path, "[archive, archive]"), "review")

    assert _status(results, "PCT-007") == ["FAIL"]
    assert "repeats surfaces" in _message(results, "PCT-007")


# --- P1-5: the validator must not ignore an argument it was given -----------


def test_pct_cli_honours_profile():
    proc = _run_pct(str(FIXTURES_DIR / "memory_profiles"), "--profile", "does_not_exist")

    assert proc.returncode == 1
    assert "does_not_exist" in proc.stdout


def test_pct_cli_accepts_a_valid_profile():
    assert _run_pct(str(FIXTURES_DIR / "memory_profiles"), "--profile", "incident").returncode == 0


def test_pct_cli_rejects_an_unknown_flag():
    assert _run_pct(str(FIXTURES_DIR / "memory_profiles"), "--bogus").returncode == 2


# --- P1-6: a fenced code block is content, not a section boundary -----------

FENCED = (
    "# Playbook\n\n"
    "## Review\n\n"
    "Check invariants.\n\n"
    f"{FENCE}bash\n"
    "## Not a real section\n"
    "echo hi\n"
    f"{FENCE}\n\n"
    "More review content.\n\n"
    "## Onboarding\n\n"
    "Read first.\n"
)


def test_fenced_heading_is_not_a_section():
    _, sections = mica_primitives.parse_markdown_sections(FENCED)

    assert sorted(sections) == ["Onboarding", "Review"]


def test_selection_is_not_truncated_by_a_fenced_heading():
    delivered, missing = mica_primitives.select_markdown_sections(FENCED, ["Review"])

    assert not missing
    assert "More review content." in delivered
    assert "echo hi" in delivered
    assert "Read first." not in delivered


@pytest.mark.parametrize("fence", [chr(96) * 3, "~~~", chr(96) * 4])
def test_fence_variants_are_tracked(fence: str):
    text = f"# T\n\n## A\n\n{fence}\n## Fake\n{fence}\n\ntail\n"
    _, sections = mica_primitives.parse_markdown_sections(text)

    assert sorted(sections) == ["A"]


# --- P1-7: coverage means every invoked surface -----------------------------


def test_partial_evidence_is_not_reported_as_exact(tmp_path: Path):
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "memory_profiles", root)
    playbook = root / "memory" / "mica_playbook.md"
    playbook.unlink()
    playbook.mkdir()

    row = mica_measure.measure(root)

    assert row["surfaces"]["invoked"] > row["capsule_coverage"]["surfaces_with_digest"]
    assert not row["capsule_coverage"]["identifies_exact_bytes"]


def test_measure_exits_nonzero_when_a_root_cannot_be_read(tmp_path: Path):
    proc = subprocess.run(
        [
            sys.executable,
            str(TOOLS_DIR / "mica_measure.py"),
            str(FIXTURES_DIR / "memory_profiles"),
            str(tmp_path / "does_not_exist"),
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    assert "could not be measured" in proc.stdout


# --- P2-8: a spec with no version number is not comparable ------------------


def test_malformed_spec_is_reported():
    """The check this belonged to was rebuilt in v3.0.1 around supported
    contracts rather than version distance. The original finding stands: a spec
    with no version number must be reported, not silently treated as current."""
    results = mica_core._spec_compatibility_result("not-a-version")

    assert results
    assert results[0][1] == "WARN"
    assert "not a version number" in results[0][2]
