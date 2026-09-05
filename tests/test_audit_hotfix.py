"""Counter-examples from the v0.2.10 audit, each one reproduced before it was fixed.

Every test here failed against `v0.2.10` and describes a way the contract said
CLOSED while the session did not, in fact, get the memory it was promised -- or
got memory it was never supposed to see.

The audit falsified one specific claim: that a closed contract means the
declared surfaces resolved. It did not, three separate ways.
"""

from __future__ import annotations

import builtins
import contextlib
import io
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core  # noqa: E402
import mica_handoff  # noqa: E402
import mica_runtime  # noqa: E402


def _copy(tmp_path: Path, fixture: str = "memory_profiles") -> Path:
    root = tmp_path / "pkg"
    shutil.copytree(FIXTURES_DIR / fixture, root)
    return root


def _axes(root: Path, profile: str | None = None) -> dict[str, str]:
    with contextlib.redirect_stdout(io.StringIO()):
        return mica_core.evaluate_axes(mica_core.run_pct_checks(root, profile))


def _check(root: Path, check_id: str, profile: str | None = None) -> tuple[str, str]:
    with contextlib.redirect_stdout(io.StringIO()):
        results = mica_core.run_pct_checks(root, profile)
    return next(((s, m) for c, s, m in results if c == check_id), ("ABSENT", ""))


# --- P0-1: a required surface with no path -----------------------------------


def test_a_required_layer_without_a_path_fails_the_contract(tmp_path: Path):
    """PCT-003 skipped any layer whose `path` was not a string, and nothing else
    in the chain looks at files. Deleting `path:` from the archive made the
    surface invisible rather than unresolvable, and the contract closed."""
    root = _copy(tmp_path)
    yaml_path = root / "mica.yaml"
    lines = yaml_path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [
        line
        for index, line in enumerate(lines)
        if not (
            line.strip().startswith("path:")
            and "archive" in "".join(lines[max(0, index - 2) : index])
        )
    ]
    # Path.write_text(newline=...) landed in 3.10, and this project supports 3.9.
    yaml_path.write_text("".join(kept), encoding="utf-8")

    status, message = _check(root, "PCT-003")

    assert status == "FAIL"
    assert "no usable path" in message
    assert _axes(root)["contract"] == "INCOMPLETE"


def test_a_declared_path_still_passes(tmp_path: Path):
    """The tightening must not fail packages whose paths are fine."""
    assert _check(_copy(tmp_path), "PCT-003")[0] == "PASS"


# --- P0-2: operator-only surfaces reaching the agent -------------------------


def test_an_empty_agent_context_is_not_refilled_with_operator_surfaces(tmp_path: Path):
    """An empty resolved agent context used to be refilled with every loaded
    surface, so a package that marked archive and playbook operator-only handed
    the agent exactly those two."""
    root = _copy(tmp_path)
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace(
            "invocation_protocol:",
            "invocation_protocol:\n"
            "  agent_context_surfaces: []\n"
            "  operator_only_surfaces: [archive, playbook]",
            1,
        ),
        encoding="utf-8",
    )

    summary = mica_runtime.build_summary(root)

    assert summary["agent_context_surfaces"] == []
    leaked = set(summary["agent_context_surfaces"]) & set(summary["operator_only_surfaces"])
    assert not leaked


def test_naming_one_surface_both_audiences_fails_rather_than_resolving(tmp_path: Path):
    """This path was already correct and is pinned so the P0-2 fix does not
    later get "simplified" into silently dropping the surface. A package that
    calls the same surface agent-context and operator-only has stated a
    contradiction, and resolving it quietly would let that config appear to
    work."""
    root = _copy(tmp_path)
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace(
            "invocation_protocol:",
            "invocation_protocol:\n  operator_only_surfaces: [playbook]",
            1,
        ),
        encoding="utf-8",
    )

    status, message = _check(root, "PCT-007")

    assert status == "FAIL"
    assert "operator_only surfaces overlap agent_context" in message
    assert _axes(root)["contract"] == "INCOMPLETE"


# --- P0-3: an invalid or stale handoff being delivered -----------------------


def _handoff(tmp_path: Path, mutate, rehash: bool = True) -> Path:
    root = _copy(tmp_path, "handoff_surface")
    path = root / "memory" / "mica_handoff.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    mutate(record)
    if rehash:
        record["handoff_hash"] = mica_handoff.compute_handoff_hash(record)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return root


@pytest.mark.parametrize(
    "label,mutate,rehash",
    [
        ("expired", lambda r: r.__setitem__("expires_at_utc", "2020-01-01T00:00:00Z"), True),
        ("superseded", lambda r: r.__setitem__("state", "superseded"), True),
        ("tampered", lambda r: r.__setitem__("unresolved", ["forged"]), False),
    ],
)
def test_a_handoff_that_is_not_current_is_withheld(tmp_path: Path, label, mutate, rehash):
    """HND-* was a standalone command wired to nothing. An expired handoff and
    one whose hash had been rewritten were both delivered like a valid one."""
    root = _handoff(tmp_path, mutate, rehash)

    summary = mica_runtime.build_summary(root, "resume")

    assert "handoff" not in summary["agent_context_surfaces"], label
    assert summary["handoff_withheld_reason"], "the reason must be reported, not silent"


@pytest.mark.parametrize(
    "label,mutate,rehash",
    [
        ("expired", lambda r: r.__setitem__("expires_at_utc", "2020-01-01T00:00:00Z"), True),
        ("tampered", lambda r: r.__setitem__("unresolved", ["forged"]), False),
    ],
)
def test_the_contract_agrees_with_the_runtime_about_a_withheld_handoff(
    tmp_path: Path, label, mutate, rehash
):
    """Reporting CLOSED while the runtime withholds the surface would make the
    two disagree about the same session."""
    root = _handoff(tmp_path, mutate, rehash)

    status, message = _check(root, "PCT-007", "resume")

    assert status == "FAIL", label
    assert "withheld" in message
    assert _axes(root, "resume")["contract"] == "INCOMPLETE"


def test_a_valid_current_handoff_is_still_delivered():
    """The gate must withhold the bad ones only."""
    summary = mica_runtime.build_summary(FIXTURES_DIR / "handoff_surface", "resume")

    assert "handoff" in summary["agent_context_surfaces"]
    assert not summary["handoff_withheld_reason"]
    assert _axes(FIXTURES_DIR / "handoff_surface", "resume")["contract"] == "CLOSED"


# --- P1-4: two layers claiming the same role ---------------------------------


def test_a_duplicate_surface_role_fails_the_contract(tmp_path: Path):
    """The runtime's path map is a dict keyed by role, so a second declaration
    overwrote the first. A decoy file could stand in for the playbook and become
    the recorded evidence while the contract still closed."""
    root = _copy(tmp_path)
    (root / "memory" / "decoy.md").write_text("## Decoy\n\nnot the playbook\n", encoding="utf-8")
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace(
            "invocation_protocol:",
            "  - name: playbook\n    path: memory/decoy.md\n    format: markdown\n"
            "    loading_hint: always\n\ninvocation_protocol:",
            1,
        ),
        encoding="utf-8",
    )

    status, message = _check(root, "PCT-007")

    assert status == "FAIL"
    assert "declared more than once" in message
    assert _axes(root)["contract"] == "INCOMPLETE"


# --- P1-5: what the capsule hash actually covers ------------------------------


def test_the_capsule_hash_covers_the_project_it_claims():
    """`project` is a required capsule field that sat outside the hash, so the
    recorded name and version could be rewritten with IVC-003/004 still passing:
    the capsule attested to an invocation of something else."""
    import mica_evidence

    assert "project" in mica_evidence._CAPSULE_HASH_FIELDS


def test_rewriting_the_project_breaks_the_capsule_hash():
    import mica_evidence

    capsule = {
        field: {} if field == "project" else f"value-for-{field}"
        for field in mica_evidence._CAPSULE_HASH_FIELDS
    }
    capsule["project"] = {"name": "real", "version": "1.0.0"}
    original = mica_evidence.compute_capsule_hash(capsule)

    capsule["project"] = {"name": "impostor", "version": "1.0.0"}

    assert mica_evidence.compute_capsule_hash(capsule) != original


def test_every_required_capsule_field_is_hashed_or_deliberately_excluded():
    """project_root is machine-specific and excluded on purpose. Anything else
    outside the hash is an assertion nothing protects."""
    import mica_evidence

    excluded = set(mica_evidence._INVOCATION_REQUIRED_FIELDS) - set(
        mica_evidence._CAPSULE_HASH_FIELDS
    )

    assert excluded == {"project_root"}, f"unprotected required capsule fields: {excluded}"


# --- P1-8: ids that collide within a second ----------------------------------


def test_two_handoffs_built_in_the_same_second_get_different_ids():
    """The id was a second-resolution timestamp, so anything faster than one per
    second produced duplicates."""
    ids = {mica_handoff.build_handoff("scope", "inv_1")["handoff_id"] for _ in range(20)}

    assert len(ids) == 20


def test_a_generated_handoff_id_still_matches_the_shipped_schema():
    import re

    schema = json.loads(
        (REPO_ROOT / "schemas" / "mica.handoff.schema.json").read_text(encoding="utf-8")
    )
    pattern = schema["properties"]["handoff_id"]["pattern"]

    assert re.fullmatch(pattern, mica_handoff.build_handoff("scope", "inv_1")["handoff_id"])


# --- P1-7: handoff validation weaker than its own schema ---------------------


def test_a_handoff_field_the_schema_forbids_is_rejected(tmp_path: Path):
    """The schema declares additionalProperties false. The validator did not,
    so a handoff could carry anything as long as the hash covered it."""
    root = _handoff(tmp_path, lambda r: r.__setitem__("smuggled", "payload"))

    results = {check: status for check, status, _ in mica_handoff.run_handoff_checks(root)}

    assert results["HND-002"] == "FAIL"


def test_an_expiry_without_a_timezone_is_reported_not_a_crash(tmp_path: Path):
    """Comparing a naive timestamp to an aware one raised TypeError and took the
    whole validation down."""
    root = _handoff(tmp_path, lambda r: r.__setitem__("expires_at_utc", "2027-01-01T00:00:00"))

    results = {check: status for check, status, _ in mica_handoff.run_handoff_checks(root)}

    assert results["HND-003"] == "WARN"


def test_an_unparseable_expiry_is_not_treated_as_no_expiry(tmp_path: Path):
    """Falling back to "no expiry declared" let a handoff with a broken date be
    delivered as current."""
    root = _handoff(tmp_path, lambda r: r.__setitem__("expires_at_utc", "next tuesday"))

    status = next(s for c, s, _ in mica_handoff.run_handoff_checks(root) if c == "HND-003")

    assert status == "WARN"


# --- P2-9: reporting that does not quietly succeed ---------------------------


def test_measure_json_exits_nonzero_when_a_root_was_skipped(tmp_path: Path):
    """The skipped-root exit lived only on the human path, so a fleet reading
    that dropped packages still reported success to whatever parsed it."""
    import subprocess

    proc = subprocess.run(
        [sys.executable, "tools/mica_measure.py", str(tmp_path / "missing"), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1


def test_the_selection_basis_reaches_the_runtime_summary():
    """It existed only inside the contract, so nothing consuming runtime JSON
    could see why a surface was left out."""
    summary = mica_runtime.build_summary(FIXTURES_DIR / "memory_profiles")

    assert set(summary["deferred_surfaces"]) == set(summary["deferred_surfaces_basis"])


# =============================================================================
# Second audit, against v3.0.0
# =============================================================================


# --- selection is a request, whatever `required` says ------------------------


def test_an_optional_surface_a_profile_selected_must_resolve(tmp_path: Path):
    """`required: false` exempts a layer from being verified by default. It was
    also exempting one the active profile had named, so PCT-003 passed while the
    runtime reported the surface missing."""
    root = _copy(tmp_path)
    yaml_path = root / "mica.yaml"
    text = yaml_path.read_text(encoding="utf-8")
    text = text.replace(
        "  - id: lessons\n    kind: lessons\n    path: memory/lessons.md\n",
        "  - id: lessons\n    kind: lessons\n    path: memory/lessons.md\n    required: false\n",
        1,
    )
    yaml_path.write_text(text, encoding="utf-8")
    (root / "memory" / "lessons.md").unlink()

    status, _ = _check(root, "PCT-003", "review")  # the review profile names lessons

    assert status == "FAIL"
    assert _axes(root, "review")["contract"] == "INCOMPLETE"


def test_an_optional_surface_no_profile_selected_stays_exempt(tmp_path: Path):
    """The tightening must not make every optional layer mandatory."""
    root = _copy(tmp_path)
    yaml_path = root / "mica.yaml"
    text = yaml_path.read_text(encoding="utf-8")
    text = text.replace(
        "  - id: lessons\n    kind: lessons\n    path: memory/lessons.md\n",
        "  - id: lessons\n    kind: lessons\n    path: memory/lessons.md\n    required: false\n",
        1,
    )
    yaml_path.write_text(text, encoding="utf-8")
    (root / "memory" / "lessons.md").unlink()

    # `default` does not name lessons
    assert _check(root, "PCT-003", "default")[0] == "PASS"
    assert _axes(root, "default")["contract"] == "CLOSED"


# --- the shipped schemas are actually applied --------------------------------


def test_a_trace_field_the_schema_forbids_is_rejected(tmp_path: Path):
    """IVC-000 confirmed the schema file was on disk; nothing applied it."""
    import mica_evidence

    root = _copy(tmp_path, "invocation_capsule_v2")
    trace = root / "memory" / "mica.invocation.jsonl"
    records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    records[0]["field_the_schema_forbids"] = "smuggled"
    records[0]["capsule_hash"] = mica_evidence.compute_capsule_hash(records[0])
    trace.write_text(
        "\n".join(json.dumps(r, separators=(",", ":"), sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )

    results = {c: s for c, s, _ in mica_evidence.run_invocation_trace_checks(trace)}

    assert results["IVC-006"] == "FAIL"


def test_a_handoff_the_schema_rejects_does_not_reach_the_agent(tmp_path: Path):
    """An empty project_scope is invalid per the shipped schema, and every
    hand-written HND check passed it through to agent context."""
    root = _handoff(tmp_path, lambda r: r.__setitem__("project_scope", ""))

    results = {c: s for c, s, _ in mica_handoff.run_handoff_checks(root)}
    summary = mica_runtime.build_summary(root, "resume")

    assert results["HND-005"] == "FAIL"
    assert "handoff" not in summary["agent_context_surfaces"]


def test_one_function_decides_handoff_delivery():
    """This logic existed twice -- once for the contract verdict, once for
    delivery -- and fixing one left the other wrong."""
    assert mica_runtime.handoff_is_deliverable is mica_core.handoff_is_deliverable


# --- a trace is provenance, so it is validated before it is written ----------


def test_the_runtime_refuses_to_write_an_incoherent_trace(tmp_path: Path):
    """Two roles pointing at one file produced a capsule the standalone
    validator rejected -- after the runtime had already appended it and exited
    zero, leaving a false account of the session on disk."""
    root = _copy(tmp_path)
    yaml_path = root / "mica.yaml"
    yaml_path.write_text(
        yaml_path.read_text(encoding="utf-8").replace(
            "  - id: playbook\n    kind: playbook\n    path: memory/mica_playbook.md\n",
            "  - id: playbook\n    kind: playbook\n    path: memory/mica_archive.json\n",
            1,
        ),
        encoding="utf-8",
    )
    summary = mica_runtime.build_summary(root)

    with pytest.raises(RuntimeError, match="incoherent invocation trace"):
        mica_runtime.write_invocation_trace(root, summary)

    assert not (root / "memory" / "mica.invocation.jsonl").exists()


def test_a_coherent_trace_is_still_written(tmp_path: Path):
    root = _copy(tmp_path)

    path = mica_runtime.write_invocation_trace(root, mica_runtime.build_summary(root))

    assert path.exists()


def test_schema_validation_dependency_failure_is_not_a_valid_verdict(
    monkeypatch: pytest.MonkeyPatch,
):
    """A vendored validator without jsonschema must fail closed, not print
    SKIP followed by an overall VALID verdict or deliver a handoff."""
    import mica_evidence

    real_import = builtins.__import__

    def import_without_jsonschema(name, *args, **kwargs):
        if name == "jsonschema" or name.startswith("jsonschema."):
            raise ImportError("blocked for regression test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_jsonschema)
    trace = FIXTURES_DIR / "invocation_capsule_v2" / "memory" / "mica.invocation.jsonl"

    trace_results = {c: s for c, s, _ in mica_evidence.run_invocation_trace_checks(trace)}
    deliverable, _ = mica_core.handoff_is_deliverable(FIXTURES_DIR / "handoff_surface")

    assert trace_results["IVC-006"] == "FAIL"
    assert not deliverable


def test_missing_handoff_validator_fails_closed(monkeypatch: pytest.MonkeyPatch):
    real_import = builtins.__import__

    def import_without_handoff(name, *args, **kwargs):
        if name == "mica_handoff":
            raise ImportError("blocked for regression test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_handoff)

    deliverable, reason = mica_core.handoff_is_deliverable(FIXTURES_DIR / "handoff_surface")

    assert not deliverable
    assert "validator unavailable" in reason


def test_handoff_json_mode_preserves_invalid_exit_status(tmp_path: Path):
    import subprocess

    root = _handoff(tmp_path, lambda record: record.__setitem__("project_scope", ""))

    proc = subprocess.run(
        [sys.executable, "tools/mica_handoff.py", str(root), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    assert json.loads(proc.stdout)["project_scope"] == ""


def test_invocation_timestamp_format_is_enforced(tmp_path: Path):
    """JSON Schema `format` is annotation-only without a FormatChecker."""
    import mica_evidence

    source = FIXTURES_DIR / "invocation_capsule_v2" / "memory" / "mica.invocation.jsonl"
    record = json.loads(source.read_text(encoding="utf-8").splitlines()[0])
    record["timestamp_utc"] = "not-a-date"
    record["capsule_hash"] = mica_evidence.compute_capsule_hash(record)
    trace = tmp_path / "mica.invocation.jsonl"
    trace.write_text(json.dumps(record) + "\n", encoding="utf-8")

    results = {c: s for c, s, _ in mica_evidence.run_invocation_trace_checks(trace)}

    assert results["IVC-006"] == "FAIL"


def test_writer_uses_the_standalone_surface_set_rules(tmp_path: Path):
    """The first pre-write gate called only the capsule helpers and omitted
    the outer validator's loaded/deferred and loaded/missing overlap rules."""
    root = _copy(tmp_path)
    summary = mica_runtime.build_summary(root)
    summary["deferred_surfaces"] = [summary["loaded_surfaces"][0]]
    output = root / "audit-trace.jsonl"

    with pytest.raises(RuntimeError, match="incoherent invocation trace"):
        mica_runtime.write_invocation_trace(root, summary, output)

    assert not output.exists()


# --- the guides describe the contract the code implements --------------------


@pytest.mark.parametrize(
    "document,section_heading",
    [
        ("docs/MICA_CROSS_REPO_ADOPTION_GUIDE.md", "## What the loader should do"),
        ("docs/MICA_CONSUMER_AUTHORING_GUIDE.md", "## AI Maintainer Contract"),
        ("templates/MICA_AGENT_GUIDE.md", "## Session Start"),
    ],
)
def test_a_loader_guide_puts_the_profile_before_loading_hint(document: str, section_heading: str):
    """All three told an external loader to take every `always` layer without
    mentioning profiles at all. A consumer AI following them loads more context
    than the package intends, and it looks correct while doing it."""
    text = (REPO_ROOT / document).read_text(encoding="utf-8")
    section = text.split(section_heading, 1)[1].split("\n## ", 1)[0]
    profile_position = section.lower().index("profile")
    always_match = re.search(r"(?:loading_hint:\s*)?`?always`?", section, re.IGNORECASE)

    assert always_match is not None, f"{document} never explains the no-profile fallback"
    always_position = always_match.start()
    assert profile_position < always_position, (
        f"{document} instructs loading `always` layers before it explains that "
        "the active profile decides"
    )
