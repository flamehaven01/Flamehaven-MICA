from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
FIXTURE_ROOT = REPO_ROOT / "fixtures" / "implicit_primary_pattern"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mica_core
import mica_runtime


def _explicit_readme_package(tmp_path: Path) -> Path:
    root = tmp_path / "pkg"
    shutil.copytree(REPO_ROOT / "templates" / "minimal-package", root)
    return root


def _pct007(root: Path) -> tuple[str, str]:
    return next(
        (status, message)
        for check, status, message in mica_core.run_pct_checks(root)
        if check == "PCT-007"
    )


def test_explicit_readme_protocol_requires_a_readme(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    (root / "README.md").unlink()

    status, message = _pct007(root)

    assert status == "FAIL"
    assert "README.md missing" in message


def test_readme_prose_is_not_an_invocation_directive(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    (root / "README.md").write_text("Read mica.yaml before work.\n", encoding="utf-8")

    status, message = _pct007(root)

    assert status == "FAIL"
    assert "lacks <!-- MICA:INVOKE" in message


def test_readme_protocol_resolves_one_manifest_pointer(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)

    status, message = _pct007(root)

    assert status == "PASS"
    assert "entrypoint=README.md -> mica.yaml" in message


def test_readme_protocol_rejects_duplicate_directives(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    readme = root / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") * 2, encoding="utf-8")

    status, message = _pct007(root)

    assert status == "FAIL"
    assert "contains 2 MICA:INVOKE directives" in message


def test_readme_protocol_rejects_a_different_manifest(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            'manifest="mica.yaml"', 'manifest="memory/mica.yaml"'
        ),
        encoding="utf-8",
    )

    status, message = _pct007(root)

    assert status == "FAIL"
    assert "but package resolves mica.yaml" in message


def test_readme_protocol_rejects_a_path_escape(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            'manifest="mica.yaml"', 'manifest="../mica.yaml"'
        ),
        encoding="utf-8",
    )

    status, message = _pct007(root)

    assert status == "FAIL"
    assert "escapes the package" in message


def test_readme_protocol_supports_a_manifest_under_memory(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    (root / "mica.yaml").replace(root / "memory" / "mica.yaml")
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            'manifest="mica.yaml"', 'manifest="memory/mica.yaml"'
        ),
        encoding="utf-8",
    )

    status, message = _pct007(root)

    assert status == "PASS"
    assert "entrypoint=README.md -> memory/mica.yaml" in message


def test_readme_protocol_requires_the_directive_near_the_top(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    readme = root / "README.md"
    readme.write_text("x" * 8193 + readme.read_text(encoding="utf-8"), encoding="utf-8")

    status, message = _pct007(root)

    assert status == "FAIL"
    assert "after the first 8192 bytes" in message


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


def test_context_format_emits_archive_and_playbook_bytes():
    summary = mica_runtime.build_summary(REPO_ROOT / "templates" / "minimal-package")

    context = mica_runtime.emit_context(REPO_ROOT / "templates" / "minimal-package", summary)

    assert "role=archive path=memory/mica_archive.json" in context
    assert "replace-with-a-real-decision" in context
    assert "role=playbook path=memory/mica_playbook.md" in context
    assert "When memory and reality disagree" in context


def test_context_cli_preserves_crlf_surface_bytes(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    archive = root / "memory" / "mica_archive.json"
    playbook = root / "memory" / "mica_playbook.md"
    archive_bytes = archive.read_bytes().replace(b"\n", b"\r\n")
    playbook_bytes = playbook.read_bytes().replace(b"\n", b"\r\n")
    archive.write_bytes(archive_bytes)
    playbook.write_bytes(playbook_bytes)

    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS_DIR / "mica_runtime.py"),
            str(root),
            "--format",
            "context",
        ],
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr.decode()
    assert archive_bytes in result.stdout
    assert playbook_bytes in result.stdout


def test_context_format_emits_only_the_selected_playbook_sections():
    root = REPO_ROOT / "fixtures" / "memory_profiles"
    summary = mica_runtime.build_summary(root, "incident")

    context = mica_runtime.emit_context(root, summary)

    assert "## Incident Runbook" in context
    assert "## Review" not in context
    assert "## Onboarding" not in context
    assert "role=lessons" not in context


def test_context_format_refuses_an_incomplete_contract(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    (root / "README.md").unlink()
    summary = mica_runtime.build_summary(root)

    try:
        mica_runtime.emit_context(root, summary)
    except RuntimeError as exc:
        assert "contract is incomplete" in str(exc)
    else:
        raise AssertionError("incomplete invocation contract emitted context")


def test_contract_refuses_non_utf8_agent_context(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    (root / "memory" / "mica_playbook.md").write_bytes(b"\xff\xfe")

    results = mica_core.run_pct_checks(root)
    status, message = next(
        (status, message) for check, status, message in results if check == "PCT-003"
    )

    assert status == "FAIL"
    assert "agent-context surface is not UTF-8" in message
    assert not mica_core.is_closed_contract(results)


def test_context_format_refuses_bytes_changed_after_resolution(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    summary = mica_runtime.build_summary(root)
    playbook = root / "memory" / "mica_playbook.md"
    playbook.write_text(playbook.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")

    try:
        mica_runtime.emit_context(root, summary)
    except RuntimeError as exc:
        assert "bytes changed after resolution" in str(exc)
    else:
        raise AssertionError("mutated context was emitted")


def test_context_cli_emits_nothing_for_an_incomplete_contract(tmp_path: Path):
    root = _explicit_readme_package(tmp_path)
    (root / "README.md").unlink()

    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS_DIR / "mica_runtime.py"),
            str(root),
            "--format",
            "context",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "invocation contract is incomplete" in result.stderr
