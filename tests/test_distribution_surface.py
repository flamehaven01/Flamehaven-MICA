"""Checks the small public surface that teaches another AI to use MICA."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from mica_primitives import MICA_TOOL_VERSION  # noqa: E402


def _skill_frontmatter() -> dict[str, str]:
    text = (REPO_ROOT / "skills" / "mica-context" / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "mica-context skill needs YAML frontmatter"
    return yaml.safe_load(match.group(1))


def _consumer_workflow() -> dict:
    path = REPO_ROOT / ".github" / "workflows" / "mica-consumer.yml"
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_mica_context_skill_has_a_discoverable_identity():
    frontmatter = _skill_frontmatter()

    assert frontmatter == {
        "name": "mica-context",
        "description": frontmatter["description"],
    }
    assert "repository" in frontmatter["description"].lower()
    assert "mica" in frontmatter["description"].lower()


def test_consumer_workflow_invokes_the_same_release_it_documents():
    workflow = _consumer_workflow()
    steps = workflow["jobs"]["invoke"]["steps"]
    mica_checkout = next(
        step
        for step in steps
        if step.get("with", {}).get("repository") == "flamehaven01/Flamehaven-MICA"
    )

    assert mica_checkout["with"]["ref"] == f"v{MICA_TOOL_VERSION}"
    assert "workflow_call" in workflow["on"]


def test_consumer_workflow_keeps_memory_out_of_published_artifacts():
    workflow = _consumer_workflow()
    serialized = (REPO_ROOT / ".github" / "workflows" / "mica-consumer.yml").read_text(
        encoding="utf-8"
    )

    assert workflow["permissions"] == {"contents": "read"}
    assert "upload-artifact" not in serialized
    assert "$RUNNER_TEMP/mica-context.bin" in serialized
    assert "--format context" in serialized
    assert "MICA emitted context bytes" in serialized


def test_repository_and_consumer_workflows_use_the_same_action_generation():
    expected = {"actions/checkout@v7", "actions/setup-python@v7"}

    for relative in (".github/workflows/ci.yml", ".github/workflows/mica-consumer.yml"):
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        uses = set(re.findall(r"uses:\s+([^\s]+)", text))
        assert expected <= uses, f"{relative} action generation drifted: {sorted(uses)}"


def test_active_guides_do_not_call_the_removed_memory_authoring_cli():
    active_guides = (
        REPO_ROOT / "README.md",
        REPO_ROOT / "fixtures" / "README.md",
        REPO_ROOT / "docs" / "MICA_CONSUMER_AUTHORING_GUIDE.md",
        REPO_ROOT / "docs" / "MICA_CROSS_REPO_ADOPTION_GUIDE.md",
    )

    offenders = [
        path.relative_to(REPO_ROOT)
        for path in active_guides
        if "mica_memory.py" in path.read_text(encoding="utf-8")
    ]
    assert not offenders, f"active guides call removed mica_memory.py: {offenders}"
