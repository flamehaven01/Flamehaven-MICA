from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURE_ROOT = REPO_ROOT / "fixtures" / "implicit_primary_pattern"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core
import mica_runtime


def test_partial_invocation_protocol_warns_about_defaulted_pattern():
    results = mica_core.run_pct_checks(FIXTURE_ROOT)
    pct007 = next((status, message) for check, status, message in results if check == "PCT-007")

    assert pct007[0] == "WARN"
    assert "primary_pattern omitted" in pct007[1]
    assert mica_core.is_closed_contract(results)


def test_runtime_distinguishes_resolved_contract_from_recorded_trace(tmp_path: Path):
    summary = mica_runtime.build_summary(FIXTURE_ROOT)
    text = mica_runtime.emit_text(summary)

    assert summary["pattern"] == "readme_protocol"
    assert summary["pattern_source"] == "defaulted"
    assert summary["invocation_evidence"] == "absent"
    assert "[MICA CONTRACT RESOLVED]" in text
    assert "Resolved  : archive, playbook" in text
    assert "Trace     : absent" in text

    trace_path = tmp_path / "mica.invocation.jsonl"
    mica_runtime.write_invocation_trace(FIXTURE_ROOT, summary, trace_path)

    assert mica_runtime._invocation_evidence_status(trace_path) == "recorded"
