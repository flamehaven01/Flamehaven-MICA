"""
MICA v0.2.8 PCT fixture tests.

Each test runs run_pct_checks() against a known fixture and asserts the
expected PCT status and overall contract verdict.

Fixtures are self-contained project roots under fixtures/.
v0.2.7: compact_mode, domain_namespaced_di.
v0.2.8: doctrinal_binding, stale_archive, violation_count_incoherent.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from mica_core import is_closed_contract, run_pct_checks


def _status(results: list, check_id: str) -> str | None:
    """Return status of the FIRST result matching check_id."""
    for pid, status, _ in results:
        if pid == check_id:
            return status
    return None


def _any_warn(results: list, check_id: str) -> bool:
    """Return True if any result for check_id has status WARN."""
    return any(pid == check_id and status == "WARN" for pid, status, _ in results)


def test_valid_bound_di_is_closed():
    results = run_pct_checks(FIXTURES_DIR / "valid_bound_di")
    assert is_closed_contract(results), "valid_bound_di should be CLOSED CONTRACT"
    assert _status(results, "PCT-010") == "PASS"
    assert _status(results, "PCT-011") == "INFO"


def test_unbound_critical_di_is_closed_with_warn():
    results = run_pct_checks(FIXTURES_DIR / "unbound_critical_di")
    assert is_closed_contract(results), "unbound_critical_di should be CLOSED (PCT-010 WARN only)"
    assert _status(results, "PCT-010") == "WARN"


def test_dead_lesson_ref_is_closed_with_warn():
    results = run_pct_checks(FIXTURES_DIR / "dead_lesson_ref")
    assert is_closed_contract(results), "dead_lesson_ref should be CLOSED (PCT-011 WARN only)"
    assert _status(results, "PCT-011") == "WARN"


def test_binding_required_fail_is_incomplete():
    results = run_pct_checks(FIXTURES_DIR / "binding_required_fail")
    assert not is_closed_contract(results), "binding_required_fail should be INCOMPLETE"
    assert _status(results, "PCT-010") == "FAIL"


def test_hook_output_violations_only_is_closed():
    results = run_pct_checks(FIXTURES_DIR / "hook_output_violations_only")
    assert is_closed_contract(results), "hook_output_violations_only should be CLOSED CONTRACT"


def test_compact_mode_returns_pct001_fail_and_pct009():
    """COMPACT_MODE: no mica.yaml. PCT-001 FAIL + PCT-009 FAIL. pct=LEGACY is correct."""
    results = run_pct_checks(FIXTURES_DIR / "compact_mode")
    assert not is_closed_contract(results), "compact_mode has no mica.yaml; cannot be CLOSED"
    assert _status(results, "PCT-001") == "FAIL"
    assert _status(results, "PCT-009") == "FAIL"


def test_domain_namespaced_di_is_closed():
    """DI-EQA-xxx / DI-BIO-xxx IDs with critical_binding_required=true. PCT-010 PASS."""
    results = run_pct_checks(FIXTURES_DIR / "domain_namespaced_di")
    assert is_closed_contract(results), "domain_namespaced_di should be CLOSED CONTRACT"
    assert _status(results, "PCT-010") == "PASS"


def test_doctrinal_binding_warns_but_closed():
    """v0.2.8: critical DIs with generic prose binding. PCT-010 PASS (all bound) + WARN (doctrinal). CLOSED CONTRACT."""
    results = run_pct_checks(FIXTURES_DIR / "doctrinal_binding")
    assert is_closed_contract(results), "doctrinal_binding should be CLOSED CONTRACT"
    assert _status(results, "PCT-010") == "PASS"
    assert _any_warn(results, "PCT-010"), "PCT-010 should have a doctrinal WARN"


def test_stale_archive_pct012_warns_but_closed():
    """v0.2.8: max_archive_age_days=90, last_updated=2020-01-01. PCT-012 WARN. CLOSED CONTRACT."""
    results = run_pct_checks(FIXTURES_DIR / "stale_archive")
    assert is_closed_contract(results), "stale_archive should be CLOSED CONTRACT"
    assert _any_warn(results, "PCT-012"), "PCT-012 should WARN on stale archive"


def test_violation_count_incoherent_warns_but_closed():
    """v0.2.8: violation_count=3 but last_triggered empty. PCT-010 WARN (coherence). CLOSED CONTRACT."""
    results = run_pct_checks(FIXTURES_DIR / "violation_count_incoherent")
    assert is_closed_contract(results), "violation_count_incoherent should be CLOSED CONTRACT"
    assert _any_warn(results, "PCT-010"), "PCT-010 should WARN on incoherent violation_count"
