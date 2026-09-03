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


def test_recall_operator_review_safe_passes_pct017():
    results = run_pct_checks(FIXTURES_DIR / "flow_recall_operator_review_safe")
    assert is_closed_contract(results)
    assert _status(results, "PCT-017") == "PASS"


def test_recall_agent_context_violation_fails_pct017():
    results = run_pct_checks(FIXTURES_DIR / "flow_recall_agent_context_violation")
    assert not is_closed_contract(results)
    assert _status(results, "PCT-017") == "FAIL"


def test_runtime_text_surfaces_recall_violation_reason():
    summary = mica_runtime.build_summary(FIXTURES_DIR / "flow_recall_agent_context_violation")
    output = mica_runtime.emit_text(summary)
    assert "Flow      : FLOW_DEGRADED" in output
    assert "Promotion gate: FAIL" in output
    assert "cand_00042" in output
    assert "operator_review.state=pending" in output


def test_recall_missing_trace_warns_pct014_but_keeps_core_closed():
    results = run_pct_checks(FIXTURES_DIR / "flow_recall_enabled_missing_trace")
    assert is_closed_contract(results)
    assert _status(results, "PCT-014") == "WARN"
    assert _status(results, "PCT-017") == "INFO"


def test_runtime_text_degrades_flow_on_missing_recall_trace_only():
    summary = mica_runtime.build_summary(FIXTURES_DIR / "flow_recall_enabled_missing_trace")
    output = mica_runtime.emit_text(summary)
    assert "Core      : CLOSED" in output
    assert "Flow      : FLOW_DEGRADED" in output
    assert "Promotion gate: PASS" in output
    assert "mica.recall.jsonl missing" in output


def test_recall_incomplete_telemetry_warns_pct018_but_keeps_core_closed():
    results = run_pct_checks(FIXTURES_DIR / "flow_recall_incomplete_telemetry")
    assert is_closed_contract(results)
    assert _status(results, "PCT-014") == "PASS"
    assert _status(results, "PCT-017") == "PASS"
    assert _status(results, "PCT-018") == "WARN"


def test_runtime_text_degrades_flow_on_incomplete_telemetry_only():
    summary = mica_runtime.build_summary(FIXTURES_DIR / "flow_recall_incomplete_telemetry")
    output = mica_runtime.emit_text(summary)
    assert "Core      : CLOSED" in output
    assert "Flow      : FLOW_DEGRADED" in output
    assert "Promotion gate: PASS" in output
    assert "session_id 'sess_unlinked_999' not linked" in output
