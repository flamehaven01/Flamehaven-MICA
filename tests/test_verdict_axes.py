"""The invocation contract must not be decided by archive or flow concerns.

MICA is a memory and playbook package. Its contract is about whether declared
memory reached the session. Archive content quality and memory-authoring
integrity are supporting concerns that report on their own axes.

v3.0.0-declaration stated this in prose while the code still let governance
checks break the contract. These tests hold the code to the statement.
"""

from __future__ import annotations

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


def _axes(fixture: str) -> dict[str, str]:
    return mica_core.evaluate_axes(mica_core.run_pct_checks(FIXTURES_DIR / fixture))


# --- axis membership ---------------------------------------------------------


def test_axes_are_disjoint():
    assert not (mica_core.CONTRACT_CHECKS & mica_core.ARCHIVE_CHECKS)
    assert not (mica_core.CONTRACT_CHECKS & mica_core.FLOW_CHECKS)
    assert not (mica_core.ARCHIVE_CHECKS & mica_core.FLOW_CHECKS)


def test_contract_axis_covers_only_invocation():
    """Every contract check must answer: did the right memory reach the session?"""
    assert mica_core.CONTRACT_CHECKS == frozenset(
        {
            "PCT-001",  # contract file present
            "PCT-002",  # surfaces declared
            "PCT-003",  # surfaces resolve
            "PCT-004",  # mode/surface coherence
            "PCT-007",  # invocation protocol
            "PCT-008",  # hook carrier
            "PCT-017",  # nothing unapproved entered agent_context
        }
    )


def test_archive_quality_checks_cannot_break_the_contract():
    for check in mica_core.ARCHIVE_CHECKS:
        assert check not in mica_core.CONTRACT_CHECKS


def test_flow_checks_cannot_break_the_contract():
    for check in mica_core.FLOW_CHECKS:
        assert check not in mica_core.CONTRACT_CHECKS


def test_hard_fail_alias_is_contract_only():
    """Consumers that vendored an older tools/ copy import this name."""
    assert mica_core.HARD_FAIL_CHECKS == mica_core.CONTRACT_CHECKS


# --- fixture behaviour -------------------------------------------------------


def test_opt_in_di_strictness_fails_archive_not_contract():
    axes = _axes("binding_required_fail")

    assert axes["archive"] == "FAILED"
    assert axes["contract"] == "CLOSED"


def test_broken_promotion_provenance_fails_flow_not_contract():
    axes = _axes("flow_candidates_broken_provenance")

    assert axes["flow"] == "FAILED"
    assert axes["contract"] == "CLOSED"


def test_unapproved_memory_in_agent_context_does_break_the_contract():
    """PCT-017 is invocation, not governance: it is about what entered context."""
    axes = _axes("flow_recall_agent_context_violation")

    assert axes["contract"] == "INCOMPLETE"


def test_missing_contract_file_breaks_the_contract():
    axes = _axes("compact_mode")

    assert axes["contract"] == "INCOMPLETE"


@pytest.mark.parametrize(
    "fixture", ["valid_bound_di", "invocation_capsule_v2", "memory_first_minimal"]
)
def test_healthy_packages_close_the_contract_without_axis_failures(fixture: str):
    """Warnings are allowed on the supporting axes; failures are not.

    valid_bound_di is a v0.2.5 package and legitimately carries archive
    warnings (version lag, one doctrinal binding). Those are reported, and
    they neither fail their own axis nor touch the contract.
    """
    axes = _axes(fixture)

    assert axes["contract"] == "CLOSED"
    assert axes["archive"] != "FAILED"
    assert axes["flow"] != "FAILED"


# --- CLI exit codes ----------------------------------------------------------


def _run_cli(fixture: str, *args: str) -> int:
    return subprocess.run(
        [sys.executable, str(TOOLS_DIR / "mica_pct.py"), str(FIXTURES_DIR / fixture), *args],
        capture_output=True,
        text=True,
    ).returncode


def test_archive_failure_does_not_fail_the_run_by_default():
    assert _run_cli("binding_required_fail") == 0


def test_strict_widens_the_exit_code_to_every_axis():
    assert _run_cli("binding_required_fail", "--strict") == 1
    assert _run_cli("flow_candidates_broken_provenance", "--strict") == 1


def test_contract_failure_always_fails_the_run():
    assert _run_cli("flow_recall_agent_context_violation") == 1
    assert _run_cli("flow_recall_agent_context_violation", "--strict") == 1


def test_healthy_package_exits_zero_in_both_modes():
    assert _run_cli("invocation_capsule_v2") == 0
    assert _run_cli("invocation_capsule_v2", "--strict") == 0
