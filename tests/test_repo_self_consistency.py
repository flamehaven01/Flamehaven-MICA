"""Checks MICA runs against itself, of the kind it runs against consumers.

MICA tells consumer packages that schema, config, and docs must evolve
together, and fails them when they drift. These are the same demands turned
inward: the version the tools declare must be the version the changelog
records, and a check that ships must have a document describing it.

Neither was enforced before. The spec backlog below is what that cost.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
DOCS_DIR = REPO_ROOT / "docs"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core  # noqa: E402
import mica_primitives  # noqa: E402

# Checks that shipped before specs were written for them. This list may shrink,
# never grow: a new check without a document fails the coverage test below.
# Removing an entry is what writing its spec looks like.
SPEC_BACKLOG = frozenset(
    {
        "PCT-001",
        "PCT-002",
        "PCT-003",
        "PCT-004",
        "PCT-005",
        "PCT-006",
        "PCT-007",
        "PCT-008",
        "PCT-009",
        "PCT-010",
        "PCT-011",
        "PCT-012",
    }
)


def _emitted_checks() -> set[str]:
    """Every check id the tools can actually emit.

    Not the same as axis membership: PCT-009 is emitted but belongs to no axis,
    because it only restates which contract checks failed. Counting a summary
    on an axis would fail that axis twice for one defect.
    """
    return {
        match
        for path in TOOLS_DIR.glob("*.py")
        for match in re.findall(r"PCT-\d{3}", path.read_text(encoding="utf-8"))
    }


def _axis_checks() -> set[str]:
    return set(mica_core.CONTRACT_CHECKS | mica_core.ARCHIVE_CHECKS | mica_core.FLOW_CHECKS)


def _documented_checks() -> set[str]:
    return {
        match.group(0)
        for path in DOCS_DIR.iterdir()
        if (match := re.match(r"PCT-\d{3}", path.name))
    }


# --- the version the tools declare is the version the changelog records ------


def test_canonical_version_has_a_changelog_entry():
    """A bump with no entry, or an entry with no bump, is the drift MICA fails
    consumers for."""
    canonical = mica_primitives.MICA_CANONICAL_VERSION
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert re.search(rf"^## v{re.escape(canonical)}\b", changelog, re.MULTILINE), (
        f"MICA_CANONICAL_VERSION is {canonical} but CHANGELOG.md has no '## v{canonical}' heading"
    )


def test_the_canonical_version_is_a_release_number():
    assert re.fullmatch(r"\d+\.\d+\.\d+", mica_primitives.MICA_CANONICAL_VERSION)


# --- a check that ships has a document describing it -------------------------


def test_every_check_outside_the_backlog_has_a_spec():
    """The ratchet. Adding a check without a spec fails here; the twelve that
    predate the practice are named above rather than silently tolerated."""
    undocumented = _emitted_checks() - _documented_checks() - SPEC_BACKLOG

    assert not undocumented, (
        f"checks with no docs/PCT-XXX_*.md spec: {sorted(undocumented)}. "
        "Write the spec, or add the id to SPEC_BACKLOG with a reason."
    )


def test_the_backlog_does_not_list_checks_that_now_have_specs():
    """Writing a spec means removing its entry. Otherwise the backlog stops
    describing the real debt and the ratchet loosens."""
    stale = SPEC_BACKLOG & _documented_checks()

    assert not stale, f"these have specs and should leave SPEC_BACKLOG: {sorted(stale)}"


def test_the_backlog_only_lists_checks_that_exist():
    assert not (SPEC_BACKLOG - _emitted_checks()), (
        f"SPEC_BACKLOG names checks nothing emits: {sorted(SPEC_BACKLOG - _emitted_checks())}"
    )


def test_a_summary_check_stays_off_the_axes():
    """PCT-009 restates which contract checks failed. On an axis it would fail
    that axis a second time for the same defect, so its absence is deliberate
    and this records why."""
    assert "PCT-009" in _emitted_checks()
    assert "PCT-009" not in _axis_checks()


def test_no_check_belongs_to_two_axes():
    """Each check answers one question. Two axes would make one failure count
    twice and make the verdict ambiguous."""
    contract, archive, flow = (
        mica_core.CONTRACT_CHECKS,
        mica_core.ARCHIVE_CHECKS,
        mica_core.FLOW_CHECKS,
    )

    assert not (contract & archive)
    assert not (contract & flow)
    assert not (archive & flow)


# --- the repository is legally adoptable -------------------------------------


def test_the_project_carries_a_license():
    """A package meant to be adopted by other repositories needs one; without
    it the default is all rights reserved."""
    license_path = REPO_ROOT / "LICENSE"

    assert license_path.exists(), "LICENSE is missing"
    assert "MIT License" in license_path.read_text(encoding="utf-8")
