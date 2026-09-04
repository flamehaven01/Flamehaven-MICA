"""Executable adoption evidence for three independently shaped consumers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema.validators import validator_for

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURES_DIR = REPO_ROOT / "fixtures"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core  # noqa: E402
import mica_runtime  # noqa: E402


def _closed(root: Path, profile: str | None = None) -> bool:
    return mica_core.evaluate_axes(mica_core.run_pct_checks(root, profile))["contract"] == "CLOSED"


@pytest.mark.parametrize(
    "fixture",
    [
        "consumer_legacy_root",
        "consumer_profile_multi_playbook",
        "consumer_nested_launcher",
    ],
)
def test_consumer_archetype_matches_the_shipped_composition_schema(fixture: str):
    root = FIXTURES_DIR / fixture
    manifest = mica_core.find_mica_yaml(root)
    assert manifest is not None

    schema = json.loads((REPO_ROOT / "mica.yaml.schema.json").read_text(encoding="utf-8"))
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    errors = list(validator_class(schema).iter_errors(document))

    assert not errors, [error.message for error in errors]


def test_legacy_root_manifest_preserves_versioned_surface_paths():
    root = FIXTURES_DIR / "consumer_legacy_root"
    summary = mica_runtime.build_summary(root)
    context = mica_runtime.emit_context(root, summary)

    assert _closed(root)
    assert "path=memory/consumer.mica.v0.2.4.json" in context
    assert "path=memory/consumer-playbook.v1.md" in context


@pytest.mark.parametrize(
    "profile,selected,rejected",
    [
        ("review", "playbook-review", "playbook-incident"),
        ("incident", "playbook-incident", "playbook-review"),
    ],
)
def test_profile_selects_one_domain_playbook(profile: str, selected: str, rejected: str):
    root = FIXTURES_DIR / "consumer_profile_multi_playbook"
    summary = mica_runtime.build_summary(root, profile)
    context = mica_runtime.emit_context(root, summary)

    assert _closed(root, profile)
    assert selected in summary["agent_context_surfaces"]
    assert rejected not in summary["agent_context_surfaces"]
    assert f"role={selected}" in context
    assert f"role={rejected}" not in context


def test_nested_manifest_consumer_launcher_delegates_to_released_runtime():
    root = FIXTURES_DIR / "consumer_nested_launcher"
    launcher = root / "tools" / "invoke_mica.py"
    env = os.environ.copy()
    env["MICA_ROOT"] = str(REPO_ROOT)

    result = subprocess.run(
        [sys.executable, str(launcher), "--format", "context"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert _closed(root)
    assert "role=archive path=memory/archive.json" in result.stdout
    assert "role=playbook path=memory/playbook.md" in result.stdout


def test_nested_launcher_fails_without_an_explicit_mica_checkout():
    root = FIXTURES_DIR / "consumer_nested_launcher"
    env = os.environ.copy()
    env.pop("MICA_ROOT", None)

    result = subprocess.run(
        [sys.executable, str(root / "tools" / "invoke_mica.py"), "--format", "context"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 2
    assert "MICA_ROOT must name a released MICA checkout" in result.stderr
