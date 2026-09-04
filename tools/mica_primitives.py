#!/usr/bin/env python3
"""
MICA primitives -- shared building blocks with no MICA-internal dependencies.

Loading, hashing, path canonicalization, and markdown section handling are used
by every layer above. Keeping them here is what lets mica_evidence and
mica_flow be imported by mica_core without an import cycle:

    mica_primitives          (no internal imports)
        ^-- mica_evidence    (capsule and trace validation)
        ^-- mica_flow        (memory-authoring pipeline checks)
                ^-- mica_core (contract resolution, PCT-001..012, verdict axes)

Added at v3.0.0 Origin P3c after extracting the flow and evidence modules
produced two import cycles back into mica_core.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

MICA_CANONICAL_VERSION = "3.0.1"

MICA_TOOL_VERSION = MICA_CANONICAL_VERSION


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalized_json_text(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    result: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError("jsonl record must be an object")
        result.append(data)
    return result


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import]

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except ImportError:
        pass
    return _minimal_yaml_parse(path)


def _minimal_yaml_parse(path: Path) -> dict[str, Any]:
    """
    Best-effort YAML parser for MICA mica.yaml.
    Handles: top-level keys, nested dicts (unlimited depth), lists of dicts.
    Does NOT handle: anchors, tags, multi-line strings, flow syntax {}/{}.
    Install PyYAML for full YAML support: pip install pyyaml
    """
    tokens = _tokenize(path)
    result, _ = _parse_block(tokens, 0, 0)
    return result


# ---------------------------------------------------------------------------
# Package resolution
# ---------------------------------------------------------------------------


def _parse_block(
    tokens: list[tuple[int, str]], pos: int, min_indent: int
) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while pos < len(tokens):
        indent, content = tokens[pos]
        if indent < min_indent:
            break
        if content.startswith("- ") or ":" not in content:
            pos += 1
            continue
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip().strip('"').strip("'")
        pos += 1
        if rest:
            result[key] = _coerce(rest)
        elif pos < len(tokens) and tokens[pos][0] > indent:
            next_indent, next_content = tokens[pos]
            if next_content.startswith("- "):
                val, pos = _parse_list(tokens, pos, next_indent)
                result[key] = val
            else:
                val, pos = _parse_block(tokens, pos, next_indent)
                result[key] = val
        else:
            result[key] = None
    return result, pos


def _parse_list(tokens: list[tuple[int, str]], pos: int, item_indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while pos < len(tokens):
        indent, content = tokens[pos]
        if indent < item_indent or not content.startswith("- "):
            break
        inner = content[2:].strip()
        pos += 1
        if not inner:
            result.append(None)
            continue
        if ":" in inner:
            k, _, v = inner.partition(":")
            item: Any = {k.strip(): _coerce(v.strip().strip('"').strip("'"))}
            if pos < len(tokens) and tokens[pos][0] > indent:
                extra, pos = _parse_block(tokens, pos, tokens[pos][0])
                item.update(extra)
        else:
            item = _coerce(inner.strip('"').strip("'"))
        result.append(item)
    return result, pos


def _tokenize(path: Path) -> list[tuple[int, str]]:
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.lstrip()
        if s and not s.startswith("#"):
            result.append((len(line) - len(s), s))
    return result


def _coerce(val: str) -> Any:
    if val.lower() in ("true", "yes", "on"):
        return True
    if val.lower() in ("false", "no", "off"):
        return False
    if val.lower() in ("null", "none", "~"):
        return None
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def find_flow_artifact(project_root: Path, filename: str) -> Path | None:
    for rel in (filename, f"memory/{filename}"):
        p = project_root / rel
        if p.exists():
            return p
    return None


def find_invocation_schema() -> Path:
    return Path(__file__).resolve().parent.parent / "mica.invocation.schema.json"


def canonical_surface_path(project_root: Path, target: Path) -> str:
    """Return a repository-relative, forward-slash path for invocation evidence.

    Raises ValueError when the target escapes the project root, so that a
    surface outside the package can never be recorded as invoked evidence.
    """
    root = Path(project_root).resolve()
    resolved = Path(target).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"surface path escapes project root: {resolved}") from exc
    return relative.as_posix()


def _resolve_within_root(project_root: Path, relative: str) -> Path | None:
    """Resolve a recorded path and refuse anything outside the project root.

    The recorded path is untrusted input. Symlinks are followed by resolve(),
    so a link inside the package that points outside is rejected too.
    """
    try:
        root = Path(project_root).resolve()
        candidate = (root / relative).resolve()
        candidate.relative_to(root)
    except (ValueError, OSError):
        return None
    return candidate


def validate_against_schema(document: Any, schema_path: Path) -> tuple[str, str]:
    """Apply a shipped JSON Schema to a document, and say so when it cannot.

    The validators used to check that a schema file existed and then hand-check
    a few fields, so anything the schema forbade but the hand-check did not
    mention passed: a trace carrying an unknown field, a handoff with an empty
    project_scope. Publishing a schema and not applying it is worse than not
    publishing one, because the schema reads as the contract.

    Consumers may vendor tools/, but a validator cannot report a document as
    valid when the validation dependency is unavailable. The affected artifact
    therefore fails closed and explains which dependency is missing.
    """
    try:
        import jsonschema
    except ImportError:
        return ("FAIL", "jsonschema is not installed; the shipped schema cannot be applied")

    if not schema_path.exists():
        return ("FAIL", f"schema missing: {schema_path}")

    schema = load_json(schema_path)
    if not schema:
        return ("FAIL", f"schema unreadable: {schema_path}")

    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)

    # `format` is annotation-only unless a checker is supplied. The base
    # jsonschema install does not guarantee a date-time checker, so register a
    # small RFC 3339 subset explicitly instead of silently accepting any text.
    format_checker = jsonschema.FormatChecker()
    format_checker.checkers = dict(format_checker.checkers)
    format_checker.checkers["date-time"] = (_is_rfc3339_datetime, ())
    validator = validator_class(schema, format_checker=format_checker)
    errors = sorted(validator.iter_errors(document), key=lambda e: tuple(map(str, e.path)))
    if not errors:
        return ("PASS", f"valid against {schema_path.name}")

    preview = "; ".join(
        f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in errors[:3]
    )
    if len(errors) > 3:
        preview += f"; ... (+{len(errors) - 3} more)"
    return ("FAIL", f"{schema_path.name}: {preview}")


def _is_rfc3339_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return True  # JSON Schema's type keyword reports the type error.
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ):
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(normalized).tzinfo is not None
    except ValueError:
        return False


def hash_bytes(payload: bytes) -> tuple[str, int]:
    """Hash exactly the bytes that will be delivered. Returns (sha256, count)."""
    return f"sha256:{hashlib.sha256(payload).hexdigest()}", len(payload)


def hash_surface_bytes(target: Path) -> tuple[str, int]:
    """Hash the exact bytes selected for delivery. Returns (sha256, byte count)."""
    data = Path(target).read_bytes()
    return f"sha256:{hashlib.sha256(data).hexdigest()}", len(data)


def parse_markdown_sections(text: str) -> tuple[str, dict[str, str]]:
    """Split a markdown surface into its preamble and its `##` sections.

    Section names are the heading text. The preamble is everything before the
    first `##`; it carries the title and any framing the sections assume, so a
    sliced delivery keeps it.
    """
    preamble_lines: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        # Track fenced blocks. A "## heading" inside a code block is content,
        # not a section boundary; treating it as one truncated real sections.
        fence_match = re.match(r"^(`{3,}|~{3,})", line.lstrip())
        if fence_match:
            marker = fence_match.group(1)[0]
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
        match = None if fence else re.match(r"^##\s+(.+?)\s*$", line.rstrip("\n"))
        if match:
            current = match.group(1)
            sections.setdefault(current, []).append(line)
            continue
        if current is None:
            preamble_lines.append(line)
        else:
            sections[current].append(line)
    return "".join(preamble_lines), {name: "".join(body) for name, body in sections.items()}


def select_markdown_sections(text: str, wanted: list[str]) -> tuple[str, list[str]]:
    """Return the preamble plus the requested sections, and any that are missing.

    Slicing is what makes the playbook addressable instead of an opaque blob:
    a review session can receive the review section without the deployment
    runbook. What is delivered is what gets hashed, so the evidence describes
    the slice rather than the file it came from.
    """
    preamble, sections = parse_markdown_sections(text)
    missing = [name for name in wanted if name not in sections]
    parts = [preamble] if preamble.strip() else []
    parts.extend(sections[name] for name in wanted if name in sections)
    return "".join(parts), missing


def format_tool_banner(tool_name: str) -> str:
    return f"{tool_name} v{MICA_TOOL_VERSION}"


# Patterns that mark a real incident-grounded origin_episode.
# Any single match exempts the binding from the doctrinal WARN (v0.2.8).
