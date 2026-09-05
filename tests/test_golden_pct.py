"""A committed snapshot of what every check says about every fixture.

The unit tests assert specific behaviours. This asserts the whole surface: for
each fixture, under each profile it declares, the exact (check, status, message)
sequence MICA produces. A change anywhere in check logic shows up here as a
reviewable diff instead of passing silently because no unit test happened to
cover that fixture.

This is the guard for a defect that has already happened twice in this project:
a change that looked local altered what unrelated packages were told about
themselves, and nothing failed. Golden output was reconstructed by hand both
times, by checking out the previous commit's tools and diffing. That is what
this file automates.

Regenerate after an intentional change, and commit the diff with it:

    python tests/test_golden_pct.py --update
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"
GOLDEN_PATH = Path(__file__).resolve().parent / "golden" / "pct_output.json"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core  # noqa: E402
import mica_primitives  # noqa: E402


def _declared_profiles(package: Path) -> list[str]:
    yd = mica_primitives.load_yaml(package / "mica.yaml") or {}
    inv = yd.get("invocation_protocol")
    profiles = inv.get("profiles") if isinstance(inv, dict) else None
    return sorted(profiles) if isinstance(profiles, dict) else []


def _packages() -> list[Path]:
    return sorted(p for p in FIXTURES_DIR.iterdir() if (p / "mica.yaml").exists())


def build_golden() -> dict[str, list[list[str]]]:
    """Every fixture, every profile it declares, plus the no-profile default.

    Check output is captured rather than printed: run_pct_checks writes to
    stdout as a side effect, and the snapshot is about its return value.
    """
    snapshot: dict[str, list[list[str]]] = {}
    for package in _packages():
        for profile in [None, *_declared_profiles(package)]:
            with contextlib.redirect_stdout(io.StringIO()):
                results = mica_core.run_pct_checks(package, profile)
            snapshot[f"{package.name}|{profile}"] = _stabilise([list(row) for row in results])
    return snapshot


# PCT-012 reports an archive's age against the clock, so its message changes
# every day even when nothing in the repository does. Snapshotting it verbatim
# meant this gate passed on the day it was written and would have failed the
# next morning on unmodified code. The age is normalised; the fact that the
# check fired, and on which fixture, is still compared exactly.
_DAYS_OLD = re.compile(r"\b\d+ days old\b")
_VOLATILE = ((_DAYS_OLD, "<N> days old"),)


def _stabilise(rows: list[list[str]]) -> list[list[str]]:
    stabilised = []
    for check, status, message in rows:
        for pattern, placeholder in _VOLATILE:
            message = pattern.sub(placeholder, message)
        stabilised.append([check, status, message])
    return stabilised


def _load_golden() -> dict[str, list[list[str]]]:
    """Missing is a failure for test_golden_snapshot_exists to report, not an
    import-time crash that hides it and blocks the first generation."""
    if not GOLDEN_PATH.exists():
        return {}
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _write_golden(snapshot: dict[str, list[list[str]]]) -> None:
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    # open() rather than write_text(newline=...), which is 3.10+ while this
    # project supports 3.9. Only --update reaches here, so CI never caught it.
    with GOLDEN_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(snapshot, indent=1, sort_keys=True) + "\n")


def test_golden_snapshot_exists():
    assert GOLDEN_PATH.exists(), (
        f"{GOLDEN_PATH.relative_to(REPO_ROOT).as_posix()} is missing. "
        "Generate it with: python tests/test_golden_pct.py --update"
    )


def test_every_fixture_is_covered():
    """A new fixture that no snapshot row mentions is an untested fixture."""
    recorded = {key.split("|", 1)[0] for key in _load_golden()}

    assert recorded == {p.name for p in _packages()}, (
        "fixture set changed. Regenerate: python tests/test_golden_pct.py --update"
    )


@pytest.mark.parametrize("key", sorted(_load_golden()))
def test_check_output_matches_the_snapshot(key: str):
    """One case per fixture-and-profile, so a failure names what moved."""
    expected = _load_golden()[key]
    actual = build_golden().get(key)

    assert actual is not None, f"{key} produced no output; regenerate the snapshot"
    for position, (want, got) in enumerate(zip(expected, actual)):
        assert got == want, (
            f"{key} row {position} changed.\n"
            f"  recorded: {want}\n"
            f"  current:  {got}\n"
            "If intended: python tests/test_golden_pct.py --update, and commit the diff."
        )
    assert len(actual) == len(expected), (
        f"{key} changed length: recorded {len(expected)} checks, current {len(actual)}. "
        "If intended: python tests/test_golden_pct.py --update"
    )


def test_the_snapshot_holds_no_value_that_changes_with_the_clock():
    """The gate must fail for a code change and only for a code change.

    Written after the snapshot recorded `2437 days old` and began disagreeing
    with itself the following morning.
    """
    offenders = [
        (key, check, message)
        for key, rows in _load_golden().items()
        for check, _, message in rows
        if _DAYS_OLD.search(message)
    ]

    assert not offenders, f"clock-derived values recorded verbatim: {offenders[:3]}"


def test_messages_do_not_leak_the_host_path_style():
    """A package file is described the same way on every OS.

    canonical_surface_path() already settled on forward slashes for recorded
    evidence; check messages describing the same files follow it.
    """
    offenders = [
        (key, check, message)
        for key, rows in _load_golden().items()
        for check, _, message in rows
        if chr(92) in message or str(REPO_ROOT) in message
    ]

    assert not offenders, offenders[:5]


if __name__ == "__main__":
    if "--update" in sys.argv:
        _write_golden(build_golden())
        print(f"wrote {GOLDEN_PATH.relative_to(REPO_ROOT).as_posix()}")
    else:
        print(__doc__)
