"""
MICA v0.2.7 PCT fixture tests.

Each test runs run_pct_checks() against a known fixture and asserts the
expected PCT-010/011 status and overall contract verdict.

Fixtures are self-contained project roots under fixtures/.
v0.2.7: added compact_mode and domain_namespaced_di fixture tests.
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
    for pid, status, _ in results:
        if pid == check_id:
            return status
    return None


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
