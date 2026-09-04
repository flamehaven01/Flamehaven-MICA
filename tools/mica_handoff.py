#!/usr/bin/env python3
"""
MICA handoff surface -- bounded state carried into the next session.

A session ends knowing things the next one will need: what it produced, what it
could not finish, which memory the next session should be given. Storing that in
the archive would make unreviewed working state look like project truth, and
storing a transcript would just move the context problem downstream.

The handoff holds references and unresolved items. It cannot promote a candidate
memory, it expires, and a superseded handoff stays visible rather than silently
becoming current.

Usage:
    python mica_handoff.py [project_root]        # validate
    python mica_handoff.py [project_root] --json # emit the parsed handoff

Exit code: 0 = valid or absent, 1 = present and invalid
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from mica_primitives import (  # noqa: E402
    MICA_TOOL_VERSION,
    _is_non_empty_string,
    _normalized_json_text,
    find_flow_artifact,
    format_tool_banner,
    hash_bytes,
    load_json,
)

__version__ = MICA_TOOL_VERSION

HANDOFF_SCHEMA_VERSION = "mica.handoff.v1"
HANDOFF_FILENAME = "mica_handoff.json"

HANDOFF_STATES = ("active", "superseded", "closed")

# Reuses the observation trust vocabulary rather than inventing a second one.
# "opaque" is a bare reference; MICA never upgrades it on its own.
ARTIFACT_TRUST_TIERS = ("native", "attested", "opaque")

_REQUIRED_FIELDS = (
    "schema_version",
    "handoff_id",
    "created_at_utc",
    "project_scope",
    "source_invocation_id",
    "state",
    "handoff_hash",
)

# handoff_hash covers everything except itself.
_HASH_FIELDS = (
    "schema_version",
    "handoff_id",
    "created_at_utc",
    "project_scope",
    "source_invocation_id",
    "state",
    "artifact_refs",
    "verification_refs",
    "candidate_memory_refs",
    "unresolved",
    "next_invocation",
    "expires_at_utc",
    "prev_handoff_hash",
)


def find_handoff_schema() -> Path:
    return Path(__file__).resolve().parent.parent / "mica.handoff.schema.json"


def compute_handoff_hash(record: dict[str, Any]) -> str:
    """Deterministic hash over everything the handoff asserts."""
    payload = {field: record.get(field) for field in _HASH_FIELDS if field in record}
    return hash_bytes(_normalized_json_text(payload).encode("utf-8"))[0]


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    if not _is_non_empty_string(value):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def build_handoff(
    project_scope: str,
    source_invocation_id: str,
    *,
    artifact_refs: list[dict[str, Any]] | None = None,
    verification_refs: list[str] | None = None,
    candidate_memory_refs: list[str] | None = None,
    unresolved: list[str] | None = None,
    next_invocation: dict[str, Any] | None = None,
    expires_at_utc: str | None = None,
    prev_handoff_hash: str | None = None,
) -> dict[str, Any]:
    """Assemble a handoff record. The caller owns what goes in it."""
    now = _iso_now()
    record: dict[str, Any] = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "handoff_id": f"handoff_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        f"-{secrets.token_hex(4)}",
        "created_at_utc": now,
        "project_scope": project_scope,
        "source_invocation_id": source_invocation_id,
        "state": "active",
        "artifact_refs": [dict(ref) for ref in artifact_refs or []],
        "verification_refs": list(verification_refs or []),
        "candidate_memory_refs": list(candidate_memory_refs or []),
        "unresolved": list(unresolved or []),
        "next_invocation": next_invocation,
        "expires_at_utc": expires_at_utc,
        "prev_handoff_hash": prev_handoff_hash,
    }
    record["handoff_hash"] = compute_handoff_hash(record)
    return record


def _check_shape(record: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    missing = [f for f in _REQUIRED_FIELDS if f not in record]
    if missing:
        return [f"missing required fields {missing}"]

    if record.get("schema_version") != HANDOFF_SCHEMA_VERSION:
        issues.append(f"unsupported schema_version {record.get('schema_version')!r}")
    if record.get("state") not in HANDOFF_STATES:
        issues.append(f"invalid state {record.get('state')!r}")
    if not _parse_iso(record.get("created_at_utc")):
        issues.append("created_at_utc is not a valid timestamp")

    for position, ref in enumerate(record.get("artifact_refs") or [], start=1):
        label = f"artifact_refs[{position}]"
        if not isinstance(ref, dict):
            issues.append(f"{label}: must be an object")
            continue
        if not _is_non_empty_string(ref.get("kind")):
            issues.append(f"{label}: kind must be a non-empty string")
        if not _is_non_empty_string(ref.get("ref")):
            issues.append(f"{label}: ref must be a non-empty string")
        if ref.get("trust_tier") not in ARTIFACT_TRUST_TIERS:
            issues.append(f"{label}: invalid trust_tier {ref.get('trust_tier')!r}")

    known = set(_HASH_FIELDS) | {"handoff_hash"}
    unknown = sorted(set(record) - known)
    if unknown:
        # The schema declares additionalProperties false. The validator did not,
        # so a handoff could carry anything as long as the hash covered it.
        issues.append(f"unknown fields not permitted by the schema: {unknown}")

    expected = compute_handoff_hash(record)
    if record.get("handoff_hash") != expected:
        issues.append(
            f"handoff_hash mismatch (recorded {record.get('handoff_hash')!r}, "
            f"recomputed {expected!r})"
        )
    return issues


def _check_freshness(record: dict[str, Any]) -> tuple[str, str]:
    """A handoff that has expired or been superseded is not current state."""
    state = record.get("state")
    if state == "superseded":
        return ("WARN", "handoff is superseded; it is history, not current state")
    if state == "closed":
        return ("INFO", "handoff is closed; nothing carries forward")

    raw_expiry = record.get("expires_at_utc")
    expires = _parse_iso(raw_expiry)
    if expires is None:
        if raw_expiry is not None:
            # A malformed expiry is not "no expiry". Treating it as absent let a
            # handoff with an unparseable date be delivered as current.
            return ("WARN", f"expires_at_utc {raw_expiry!r} is not a valid timestamp")
        return ("PASS", "handoff is active with no expiry declared")
    if expires.tzinfo is None:
        # A naive timestamp used to reach the comparison below and raise
        # TypeError, taking the whole validation down with it.
        return (
            "WARN",
            f"expires_at_utc {raw_expiry!r} declares no timezone; it cannot be compared to now",
        )
    if datetime.now(timezone.utc) > expires:
        return (
            "WARN",
            f"handoff expired at {record.get('expires_at_utc')}; "
            "exclude it unless an operator reactivates it",
        )
    return ("PASS", f"handoff is active until {record.get('expires_at_utc')}")


def run_handoff_checks(target: Path) -> list[tuple[str, str, str]]:
    """Validate a handoff document. Absence is not a failure."""
    schema_path = find_handoff_schema()
    results: list[tuple[str, str, str]] = [
        (
            "HND-000",
            "PASS" if schema_path.exists() else "FAIL",
            f"handoff schema {'present' if schema_path.exists() else 'missing'} ({schema_path})",
        )
    ]

    path = target
    if target.is_dir():
        resolved = find_flow_artifact(target, HANDOFF_FILENAME)
        if not resolved:
            results.append(("HND-001", "INFO", "no handoff surface; nothing carries forward"))
            return results
        path = resolved
    if not path.exists():
        results.append(("HND-001", "INFO", f"no handoff surface at {path}"))
        return results

    record = load_json(path)
    if not record:
        results.append(("HND-001", "FAIL", f"handoff present but unreadable: {path}"))
        return results
    results.append(("HND-001", "PASS", f"handoff present ({path})"))

    issues = _check_shape(record)
    if issues:
        preview = "; ".join(issues[:4])
        if len(issues) > 4:
            preview += f"; ... (+{len(issues) - 4} more)"
        results.append(("HND-002", "FAIL", preview))
        return results
    results.append(("HND-002", "PASS", f"handoff shape valid ({record['handoff_id']})"))

    status, message = _check_freshness(record)
    results.append(("HND-003", status, message))

    # A handoff records candidates; it cannot promote them. This check exists
    # because the writer is the same session that produced the candidates.
    promoted = [
        ref for ref in record.get("candidate_memory_refs") or [] if not str(ref).startswith("cand_")
    ]
    if promoted:
        results.append(
            (
                "HND-004",
                "FAIL",
                f"candidate_memory_refs must be candidate ids, got {promoted} -- "
                "a handoff cannot promote memory",
            )
        )
    else:
        results.append(
            ("HND-004", "PASS", "candidate references are candidates, not promoted memory")
        )
    return results


def _report(results: list[tuple[str, str, str]]) -> bool:
    print()
    failed = False
    warned = False
    for cid, status, message in results:
        print(f"{cid} [{status:<4}] {message}")
        if status == "FAIL":
            failed = True
        elif status == "WARN":
            warned = True
    print()
    if failed:
        verdict = "INVALID HANDOFF"
    elif warned:
        verdict = "VALID HANDOFF (not current)"
    else:
        verdict = "VALID HANDOFF"
    print("Overall:", verdict)
    print()
    return not failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a MICA handoff surface")
    parser.add_argument("project_root", nargs="?", default=".", help="package root or handoff file")
    parser.add_argument("--json", action="store_true", help="emit the parsed handoff")
    args = parser.parse_args()

    target = Path(args.project_root).resolve()
    if args.json:
        path = find_flow_artifact(target, HANDOFF_FILENAME) if target.is_dir() else target
        print(json.dumps(load_json(path) if path else {}, indent=2))
        return

    print(format_tool_banner("MICA Handoff Validator"))
    print(f"Target: {target}")
    print(f"Schema: {find_handoff_schema()}")
    sys.exit(0 if _report(run_handoff_checks(target)) else 1)


if __name__ == "__main__":
    main()
