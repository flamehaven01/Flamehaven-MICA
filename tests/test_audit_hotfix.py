"""Counter-examples from the v0.2.10 audit, each one reproduced before it was fixed.

Every test here failed against `v0.2.10` and describes a way the contract said
CLOSED while the session did not, in fact, get the memory it was promised -- or
got memory it was never supposed to see.

The audit falsified one specific claim: that a closed contract means the
declared surfaces resolved. It did not, three separate ways.
"""

from __future__ import annotations

import contextlib
import io
import json
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
    yaml_path.write_text("".join(kept), encoding="utf-8", newline="\n")

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
