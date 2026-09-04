"""Run the commands the README shows, against the output it claims they print.

Written after the README shipped a first-run example asserting `Archive : PASS`
and `Flow : PASS` for a fixture that actually prints `Archive : OK` and
`Flow : OK` -- using a verdict word `mica_pct.py` never emits on that line. It
was never run. It was written from memory and reviewed by reading.

The first attempt at this guard did not catch it either: the expected output
lived in a list here, so editing the README could not fail anything. Expected
output is now read out of the README itself, which is the only version that
catches a README claiming something the tool does not do.

Any fenced `text` block whose first line is a `python tools/...` command is
executed, and every following non-empty line must appear in its real output.
Adding an example to the README is enough to have it verified; no list here
needs updating.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"

# Lines that are prose or elision rather than literal output.
_SKIPPABLE = ("...", "# ")


def _documented_runs() -> list[tuple[str, list[str]]]:
    blocks = re.findall(r"```text\n(.*?)```", README.read_text(encoding="utf-8"), re.DOTALL)
    runs = []
    for block in blocks:
        lines = block.splitlines()
        if not lines or not lines[0].startswith("python tools/"):
            continue
        expected = [
            line for line in lines[1:] if line.strip() and not line.strip().startswith(_SKIPPABLE)
        ]
        runs.append((lines[0], expected))
    return runs


def _run(command: str) -> subprocess.CompletedProcess[str]:
    argv = command.split()
    assert argv[0] == "python", command
    return subprocess.run(
        [sys.executable, *argv[1:]], cwd=REPO_ROOT, capture_output=True, text=True, timeout=180
    )


def test_the_readme_still_documents_runnable_examples():
    """If this drops to zero the extraction pattern went stale and every other
    test in this file silently passes on an empty set."""
    assert len(_documented_runs()) >= 3


@pytest.mark.parametrize(
    "command,expected", _documented_runs(), ids=lambda v: v if isinstance(v, str) else None
)
def test_a_documented_command_prints_what_the_readme_shows(command: str, expected: list[str]):
    result = _run(command)

    assert expected, f"{command} is documented with no output to check"
    for line in expected:
        assert line in result.stdout, (
            f"README shows this line for `{command}`:\n"
            f"  {line!r}\n"
            f"The command actually printed:\n{result.stdout}"
        )


@pytest.mark.parametrize(
    "command,expected", _documented_runs(), ids=lambda v: v if isinstance(v, str) else None
)
def test_a_documented_command_names_a_file_that_exists(command: str, expected: list[str]):
    for token in command.split()[1:]:
        if token.startswith(("tools/", "fixtures/", "tests/")):
            assert (REPO_ROOT / token).exists(), f"{command} names a missing path: {token}"


# --- every link the README makes actually resolves ---------------------------


def _local_links(text: str) -> list[str]:
    return [
        target
        for target in re.findall(r"\]\(([^)]+)\)", text)
        if not target.startswith(("http://", "https://", "#"))
    ]


def test_every_local_link_in_the_readme_resolves():
    """Moving two docs out of the published tree left two dead links behind.
    Until now this was only ever checked by hand."""
    broken = [
        target
        for target in _local_links(README.read_text(encoding="utf-8"))
        if not (REPO_ROOT / target.split("#", 1)[0]).exists()
    ]

    assert not broken, f"README links to files that do not exist: {broken}"


def test_every_local_link_in_the_changelog_resolves():
    changelog = REPO_ROOT / "CHANGELOG.md"
    broken = [
        target
        for target in _local_links(changelog.read_text(encoding="utf-8"))
        if not (REPO_ROOT / target.split("#", 1)[0]).exists()
    ]

    assert not broken, f"CHANGELOG links to files that do not exist: {broken}"


def test_every_local_link_in_the_published_docs_resolves():
    """A doc that points at a sibling which has since moved is as broken as a
    dead README link, and nothing looked at those either."""
    broken = []
    for doc in sorted((REPO_ROOT / "docs").glob("*.md")):
        for target in _local_links(doc.read_text(encoding="utf-8")):
            resolved = (doc.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                broken.append(f"{doc.name} -> {target}")

    assert not broken, "dead links inside docs/:\n  " + "\n  ".join(broken[:10])
