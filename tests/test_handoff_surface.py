"""The handoff surface: bounded state carried into the next session.

A session ends knowing what it produced and what it could not finish. Putting
that in the archive would make unreviewed working state look like project truth;
storing a transcript would move the context problem downstream instead of
solving it.

These tests hold the boundaries: a handoff expires, a superseded one stays
visible rather than silently becoming current, and it can reference a candidate
but never promote one.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core  # noqa: E402
import mica_handoff  # noqa: E402
import mica_runtime  # noqa: E402

FIXTURE = FIXTURES_DIR / "handoff_surface"


def _status(results, check_id):
    return next((s for c, s, _ in results if c == check_id), None)


def _message(results, check_id):
    return next((m for c, _, m in results if c == check_id), "")


def _mutated(tmp_path: Path, mutate, rehash: bool = True) -> Path:
    """Copy the fixture, change the handoff, and rewrite its hash like a writer would."""
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURE, root)
    path = root / "memory" / "mica_handoff.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    mutate(record)
    if rehash:
        record["handoff_hash"] = mica_handoff.compute_handoff_hash(record)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return root


# --- the surface participates in the normal contract -------------------------


def test_handoff_package_closes_its_contract():
    axes = mica_core.evaluate_axes(mica_core.run_pct_checks(FIXTURE, "resume"))

    assert axes["contract"] == "CLOSED"


def test_handoff_is_an_allowed_agent_context_surface():
    assert "handoff" in mica_core._AGENT_CONTEXT_ALLOWED_SURFACES
    assert "handoff" in mica_core._OPERATOR_ONLY_ALLOWED_SURFACES


def test_a_profile_decides_whether_the_handoff_is_delivered():
    """Resuming interrupted work needs it. A routine session does not."""
    default = mica_runtime.build_summary(FIXTURE, "default")
    resume = mica_runtime.build_summary(FIXTURE, "resume")

    assert "handoff" not in default["loaded_surfaces"]
    assert "handoff" in resume["loaded_surfaces"]
    assert "handoff" in resume["agent_context_surfaces"]


def test_the_handoff_carries_its_own_digest_in_the_capsule():
    summary = mica_runtime.build_summary(FIXTURE, "resume")
    entry = next(e for e in summary["surface_evidence"] if e["role"] == "handoff")

    assert entry["sha256"].startswith("sha256:")
    assert entry["bytes"] > 0


# --- absence is not failure --------------------------------------------------


def test_a_package_without_a_handoff_is_not_penalised(tmp_path: Path):
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / "memory_profiles", root)

    results = mica_handoff.run_handoff_checks(root)

    assert _status(results, "HND-001") == "INFO"
    assert not any(s == "FAIL" for _, s, _ in results)


def test_cli_exits_zero_when_no_handoff_exists():
    proc = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "mica_handoff.py"), str(FIXTURES_DIR / "memory_profiles")],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0


# --- shape and tamper detection ----------------------------------------------


def test_valid_handoff_passes_every_check():
    results = mica_handoff.run_handoff_checks(FIXTURE)

    assert [s for _, s, _ in results] == ["PASS"] * len(results)


def test_editing_without_rehashing_is_caught(tmp_path: Path):
    root = _mutated(tmp_path, lambda r: r.__setitem__("unresolved", ["forged"]), rehash=False)

    results = mica_handoff.run_handoff_checks(root)

    assert _status(results, "HND-002") == "FAIL"
    assert "handoff_hash mismatch" in _message(results, "HND-002")


def test_an_invalid_trust_tier_is_rejected(tmp_path: Path):
    """Trust reuses the observation vocabulary; 'trusted' is not in it."""
    root = _mutated(tmp_path, lambda r: r["artifact_refs"][0].__setitem__("trust_tier", "trusted"))

    results = mica_handoff.run_handoff_checks(root)

    assert _status(results, "HND-002") == "FAIL"
    assert "trust_tier" in _message(results, "HND-002")


def test_trust_vocabulary_matches_the_observation_schema():
    """One vocabulary, not two. A third set of trust words would be drift."""
    observe = json.loads((REPO_ROOT / "mica.observe.schema.json").read_text(encoding="utf-8"))

    assert list(mica_handoff.ARTIFACT_TRUST_TIERS) == observe["properties"]["trust_tier"]["enum"]


# --- freshness: a stale handoff is not current state -------------------------


def test_an_expired_handoff_warns(tmp_path: Path):
    root = _mutated(tmp_path, lambda r: r.__setitem__("expires_at_utc", "2020-01-01T00:00:00Z"))

    results = mica_handoff.run_handoff_checks(root)

    assert _status(results, "HND-003") == "WARN"
    assert "expired" in _message(results, "HND-003")


def test_a_superseded_handoff_is_visible_but_not_current(tmp_path: Path):
    root = _mutated(tmp_path, lambda r: r.__setitem__("state", "superseded"))

    results = mica_handoff.run_handoff_checks(root)

    assert _status(results, "HND-003") == "WARN"
    assert "history" in _message(results, "HND-003")


def test_a_closed_handoff_reports_that_nothing_carries_forward(tmp_path: Path):
    root = _mutated(tmp_path, lambda r: r.__setitem__("state", "closed"))

    assert _status(mica_handoff.run_handoff_checks(root), "HND-003") == "INFO"


@pytest.mark.parametrize("state", ["superseded", "closed"])
def test_stale_states_do_not_fail_the_run(tmp_path: Path, state: str):
    """Being out of date is not the same as being invalid."""
    root = _mutated(tmp_path, lambda r: r.__setitem__("state", state))

    proc = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "mica_handoff.py"), str(root)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0


# --- a handoff cannot promote memory -----------------------------------------


def test_a_promoted_memory_id_is_rejected(tmp_path: Path):
    """The session writing the handoff produced those candidates. It cannot
    also approve them."""
    root = _mutated(tmp_path, lambda r: r.__setitem__("candidate_memory_refs", ["mem_00003"]))

    results = mica_handoff.run_handoff_checks(root)

    assert _status(results, "HND-004") == "FAIL"
    assert "cannot promote memory" in _message(results, "HND-004")


def test_candidate_references_are_allowed(tmp_path: Path):
    root = _mutated(
        tmp_path, lambda r: r.__setitem__("candidate_memory_refs", ["cand_00001", "cand_00002"])
    )

    assert _status(mica_handoff.run_handoff_checks(root), "HND-004") == "PASS"


# --- schema ------------------------------------------------------------------


def test_handoff_schema_metavalidates():
    schema = json.loads((REPO_ROOT / "mica.handoff.schema.json").read_text(encoding="utf-8"))

    jsonschema.validators.validator_for(schema).check_schema(schema)


def test_the_written_handoff_satisfies_the_shipped_schema():
    schema = json.loads((REPO_ROOT / "mica.handoff.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.validators.validator_for(schema)(schema)
    record = json.loads((FIXTURE / "memory" / "mica_handoff.json").read_text(encoding="utf-8"))

    errors = sorted(validator.iter_errors(record), key=lambda e: list(e.path))

    assert not errors, [f"{list(e.path)}: {e.message}" for e in errors]


def test_build_handoff_produces_a_self_consistent_record():
    record = mica_handoff.build_handoff("scope", "inv_1", unresolved=["one thing"])

    assert record["handoff_hash"] == mica_handoff.compute_handoff_hash(record)
    assert record["state"] == "active"
