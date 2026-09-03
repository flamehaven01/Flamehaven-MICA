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

# --- PCT-006 must not invent a count -----------------------------------------


def _lag_message(spec: str) -> str | None:
    results = mica_core._spec_lag_result(spec)
    return results[0][2] if results else None


@pytest.mark.parametrize("spec", ["0.2.8", "0.2.7"])
def test_current_and_adjacent_specs_are_quiet(spec: str):
    assert _lag_message(spec) is None


@pytest.mark.parametrize("spec, patches", [("0.2.6", 2), ("0.2.4", 4)])
def test_same_minor_reports_a_true_patch_count(spec: str, patches: int):
    message = _lag_message(spec)

    assert message is not None
    assert f"{patches} patch version(s) behind" in message


@pytest.mark.parametrize("spec", ["0.1.9", "0.1.8", "0.0.1"])
def test_crossing_a_minor_boundary_states_no_count(spec: str):
    """0.1.9 was previously reported as 99 versions behind 0.2.8."""
    message = _lag_message(spec)

    assert message is not None
    assert "at least one minor version" in message
    for fabricated in ("99 ", "100 ", "version(s) behind canonical"):
        assert fabricated not in message


@pytest.mark.parametrize("spec", ["0.2.10", "1.0.0"])
def test_a_spec_ahead_of_canonical_is_flagged(spec: str):
    """Flamehaven-CAS declares 0.2.10, for which no canonical schema exists."""
    message = _lag_message(spec)

    assert message is not None
    assert "ahead of canonical" in message


def test_no_lag_message_claims_a_number_it_cannot_support():
    for minor in range(0, 3):
        for patch in range(0, 12):
            spec = f"0.{minor}.{patch}"
            message = _lag_message(spec)
            if message and "patch version(s) behind" in message:
                assert spec.split(".")[1] == mica_core.MICA_CANONICAL_VERSION.split(".")[1]


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
    assert "_spec_note" in source


def test_measure_surfaces_the_pct006_message_verbatim():
    row = mica_measure.measure(FIXTURES_DIR / "valid_bound_di")
    pct006 = [
        msg
        for pid, status, msg in mica_core.run_pct_checks(FIXTURES_DIR / "valid_bound_di")
        if pid == "PCT-006" and status == "WARN" and "canonical" in msg
    ]

    assert row["spec_note"] == (pct006[0] if pct006 else None)


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
