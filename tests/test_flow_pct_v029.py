from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_runtime
from mica_core import is_closed_contract, run_pct_checks


def _status(results: list[tuple[str, str, str]], check_id: str) -> str | None:
    for pid, status, _ in results:
        if pid == check_id:
            return status
    return None


def test_flow_observation_valid_passes_pct013():
    results = run_pct_checks(FIXTURES_DIR / "flow_observation_valid")
    assert is_closed_contract(results)
    assert _status(results, "PCT-013") == "PASS"
    assert _status(results, "PCT-015") == "INFO"


def test_flow_candidates_approved_lesson_passes_pct015():
    results = run_pct_checks(FIXTURES_DIR / "flow_candidates_approved_lesson")
    assert is_closed_contract(results)
    assert _status(results, "PCT-013") == "PASS"
    assert _status(results, "PCT-015") == "PASS"


def test_flow_candidates_broken_provenance_fails_pct015():
    results = run_pct_checks(FIXTURES_DIR / "flow_candidates_broken_provenance")
    assert not is_closed_contract(results)
    assert _status(results, "PCT-015") == "FAIL"


def test_runtime_text_reports_core_and_flow_for_flow_fixture():
    summary = mica_runtime.build_summary(FIXTURES_DIR / "flow_candidates_approved_lesson")
    output = mica_runtime.emit_text(summary)
    assert "Core      : CLOSED" in output
    assert "Flow      : FLOW_ENABLED" in output
    assert "Observation: PASS" in output
    assert "Promotion gate: PASS" in output
