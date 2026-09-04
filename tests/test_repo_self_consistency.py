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
#
# The ratchet used to collect `PCT-\d{3}` only, so the whole HND and IVC
# families sat outside it -- thirteen checks nothing asked about. HND-005 and
# IVC-006 were then added with no spec and nothing failed, which is exactly the
# promise this gate makes. Both now have specs; the families that predate the
# practice are frozen here.
SPEC_BACKLOG = frozenset(
    {
        # package contract
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
        # handoff surface
        "HND-000",
        "HND-001",
        "HND-002",
        "HND-003",
        "HND-004",
        # invocation evidence
        "IVC-000",
        "IVC-001",
        "IVC-002",
        "IVC-003",
        "IVC-004",
        "IVC-005",
    }
)

# Every check family the tools emit. A family missing here is a family the
# documentation gate cannot see.
CHECK_FAMILIES = ("PCT", "HND", "IVC")
_CHECK_ID = re.compile(rf"(?:{'|'.join(CHECK_FAMILIES)})-\d{{3}}")


def _emitted_checks() -> set[str]:
    """Every check id the tools can actually emit, across every family.

    Not the same as axis membership: PCT-009 is emitted but belongs to no axis,
    because it only restates which contract checks failed. Counting a summary
    on an axis would fail that axis twice for one defect.
    """
    return {
        match
        for path in TOOLS_DIR.glob("*.py")
        for match in _CHECK_ID.findall(path.read_text(encoding="utf-8"))
    }


def _axis_checks() -> set[str]:
    return set(mica_core.CONTRACT_CHECKS | mica_core.ARCHIVE_CHECKS | mica_core.FLOW_CHECKS)


def _documented_checks() -> set[str]:
    return {match.group(0) for path in DOCS_DIR.iterdir() if (match := _CHECK_ID.match(path.name))}


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
        f"checks with no docs/<ID>_*_SPEC.md: {sorted(undocumented)}. "
        "Write the spec. Adding to SPEC_BACKLOG is for checks that predate the "
        "practice, not for new ones."
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


# --- the shipped schema and the runtime describe the same contract -----------


def _composition_validator():
    import json

    import jsonschema

    schema = json.loads((REPO_ROOT / "mica.yaml.schema.json").read_text(encoding="utf-8"))
    return jsonschema.validators.validator_for(schema)(schema)


def test_every_fixture_validates_against_the_shipped_schema():
    """Nothing checked this, and 12 of 22 fixtures had drifted out of the
    published contract -- including `handoff_surface`, added the same week the
    schema was left untouched. A consumer validating against the shipped schema
    would have been rejected for a package this repository calls correct."""
    validator = _composition_validator()
    invalid = []
    for package in sorted((REPO_ROOT / "fixtures").iterdir()):
        yaml_path = package / "mica.yaml"
        if not yaml_path.exists():
            continue
        errors = sorted(validator.iter_errors(mica_primitives.load_yaml(yaml_path)), key=str)
        if errors:
            invalid.append(f"{package.name}: {errors[0].message[:90]}")

    assert not invalid, "fixtures rejected by the shipped schema:\n  " + "\n  ".join(invalid)


def test_the_schema_permits_every_surface_the_code_permits():
    """The enum listed five agent-context surfaces while the code allowed six
    plus hyphen-qualified narrowings, so `handoff` and `playbook-eqa` were both
    rejected by the schema and accepted by the runtime."""
    import re

    validator = _composition_validator()
    proto = validator.schema["$defs"]["invocationProtocol"]["properties"]
    pattern = proto["agent_context_surfaces"]["items"]["pattern"]

    for role in mica_core._AGENT_CONTEXT_ALLOWED_SURFACES:
        assert re.fullmatch(pattern, role), f"schema rejects allowed surface {role}"
    assert re.fullmatch(pattern, "playbook-eqa"), "schema rejects a specialised playbook"
    assert not re.fullmatch(pattern, "sessions"), "schema must not widen the audience boundary"


def test_the_schema_accepts_a_layer_declared_by_kind():
    """layer_role() reads `kind` before `name`, but the non-memory-first branch
    demanded `name` plus a fixed `format`."""
    validator = _composition_validator()
    document = {
        "name": "kind-declared",
        "mica_spec": mica_primitives.MICA_CANONICAL_VERSION,
        "mode": "memory_injection",
        "layers": [
            {"kind": "archive", "path": "memory/a.json"},
            {"kind": "playbook", "path": "memory/p.md"},
        ],
    }

    assert not list(validator.iter_errors(document))


# --- nothing machine-specific or private reaches the published tree ----------


def _tracked_text_files() -> list[Path]:
    import subprocess

    listing = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    paths = []
    for line in listing.stdout.splitlines():
        path = REPO_ROOT / line
        if path.suffix.lower() in {".png", ".jpg", ".gif", ".ico", ".pdf"}:
            continue
        if path.exists():
            paths.append(path)
    return paths


# Path-escape test data: these assert that an absolute path is refused, so the
# absolute path is the point.
_PATH_LITERAL_EXEMPT = {
    "test_invocation_capsule_v2.py",
    "test_schema_metavalidation.py",
    # A gate has to name what it forbids, so it matches itself.
    "test_repo_self_consistency.py",
}


def test_no_tracked_file_carries_a_local_machine_path():
    """The repository is public. Four docs shipped `D:/Sanctum/...` links that
    resolve on exactly one machine, and one of them named a private customer
    codebase."""
    drive = re.compile(r"(?:^|[^A-Za-z0-9])[A-Za-z]:[\/]")
    home = re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/")

    offenders = []
    for path in _tracked_text_files():
        if path.name in _PATH_LITERAL_EXEMPT:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = re.sub(r"https?://\S+", "", line)
            if drive.search(stripped) or home.search(stripped):
                offenders.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}:{number}: {line.strip()[:70]}"
                )

    assert not offenders, "local machine paths in tracked files:\n  " + "\n  ".join(offenders[:8])


def test_no_tracked_file_points_at_a_private_repository():
    """Naming a private repository as a "representative example" gives a public
    reader something they cannot open, and publishes the internal roster."""
    private = ("Flamehaven-CAS", "flamehaven-space")

    offenders = [
        f"{path.relative_to(REPO_ROOT).as_posix()}: {name}"
        for path in _tracked_text_files()
        if path.name not in _PATH_LITERAL_EXEMPT
        for name in private
        if name in path.read_text(encoding="utf-8")
    ]

    assert not offenders, "private repositories named in public files:\n  " + "\n  ".join(offenders)


def test_the_readme_reports_the_real_check_counts():
    """The README said "five of seventeen" while the tools emitted thirty. A
    number written by hand in prose drifts from the code the moment either
    moves, so it is asserted here instead."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    emitted, documented, backlog = _emitted_checks(), _documented_checks(), SPEC_BACKLOG

    assert f"MICA emits {len(emitted)} checks" in readme
    assert f"{len(documented)} have a spec" in readme
    assert f"The other {len(backlog)} predate" in readme


def test_every_family_the_tools_emit_is_one_the_gate_collects():
    """A family absent from CHECK_FAMILIES is a family this gate cannot see,
    which is how HND and IVC went unnoticed."""
    import re as _re

    prefixes = {
        match
        for path in TOOLS_DIR.glob("*.py")
        for match in _re.findall(r"\b([A-Z]{3})-\d{3}\b", path.read_text(encoding="utf-8"))
    }

    assert prefixes == set(CHECK_FAMILIES), (
        f"tools emit families the gate does not collect: {sorted(prefixes - set(CHECK_FAMILIES))}"
    )


def test_the_readme_reports_the_real_fixture_count():
    """The README said 23 the moment a 24th was added, and only a scratch script
    had ever checked it. Same drift as "five of seventeen shipping checks"."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    fixtures = [p for p in (REPO_ROOT / "fixtures").iterdir() if p.is_dir()]

    assert f"{len(fixtures)} fixtures cover" in readme


def test_every_fixture_appears_in_the_fixture_map():
    """fixtures/README.md is what the top-level README calls the full map. A
    fixture missing from it is undocumented, whatever the count says."""
    fixture_map = (REPO_ROOT / "fixtures" / "README.md").read_text(encoding="utf-8")
    missing = [
        path.name
        for path in sorted((REPO_ROOT / "fixtures").iterdir())
        if path.is_dir() and path.name not in fixture_map
    ]

    assert not missing, f"fixtures absent from fixtures/README.md: {missing}"


# --- the starter template is a working package -------------------------------


def test_the_minimal_template_closes_its_own_contract():
    """A starter package that does not resolve teaches the wrong thing on the
    first try, and a template nothing runs rots silently."""
    import contextlib
    import io

    template = REPO_ROOT / "templates" / "minimal-package"
    with contextlib.redirect_stdout(io.StringIO()):
        results = mica_core.run_pct_checks(template)

    assert mica_core.evaluate_axes(results)["contract"] == "CLOSED"


def test_the_minimal_template_declares_a_supported_contract():
    yaml_path = REPO_ROOT / "templates" / "minimal-package" / "mica.yaml"
    declared = mica_primitives.load_yaml(yaml_path)["mica_spec"]

    assert declared in mica_core.SUPPORTED_CONTRACT_VERSIONS


def test_the_minimal_template_validates_against_the_shipped_schema():
    yaml_path = REPO_ROOT / "templates" / "minimal-package" / "mica.yaml"
    errors = list(_composition_validator().iter_errors(mica_primitives.load_yaml(yaml_path)))

    assert not errors, [e.message for e in errors[:3]]


def test_the_readme_invocation_template_is_reachable_from_the_starter():
    """The block and the package are two halves of one thing. A reader who finds
    one has to be able to find the other: memory with no entrypoint is memory
    nothing opens."""
    starter = (REPO_ROOT / "templates" / "minimal-package" / "mica.yaml").read_text(
        encoding="utf-8"
    )

    assert "MICA_README_INVOCATION.md" in starter
    assert (REPO_ROOT / "templates" / "MICA_README_INVOCATION.md").exists()
