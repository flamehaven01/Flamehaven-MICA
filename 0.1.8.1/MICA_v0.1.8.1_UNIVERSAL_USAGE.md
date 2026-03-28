# MICA v0.1.8 Universal Usage Rules

Status: normative usage note for mica-v0.1.8-universal.schema.json
Supersedes: MICA_v0.1.7_UNIVERSAL_USAGE.md

---

## 1. When to use v0.1.8 universal

Same as v0.1.7, plus any project that needs:
- Normative AI session invocation (README-as-Protocol or Global Skill)
- Self-test validation of the archive against the real project
- Structured design invariants (id/label/statement/severity, not freeform strings)
- Provenance drift response policy
- Logical track decomposition (without MICA-LAB)

Do not use for:
- Parity-driven laboratory protocols (use mica-lab-v0.1.5.schema.json)
- Experimental track orchestration requiring explicit cycle contracts

---

## 2. Breaking changes from v0.1.7

### 2-1. `design_invariants` — items type changed

v0.1.7: `array of strings`
v0.1.8: `array of designInvariantEntry` objects

Each entry now requires:
```json
{
  "id": "DI-001",
  "label": "short name",
  "statement": "Full binding rule text.",
  "severity": "critical"
}
```
Optional: `track` (track ID), `note`

**Migration**: convert each string to an object. Assign sequential DI-nnn IDs.

### 2-2. `deviationLogEntry` — required fields relaxed

v0.1.7 required: `change_id`, `timestamp_utc`, `gate`, `reason`, `before_hash`, `after_hash`, `approved_by`, `rollback_ready`
v0.1.8 required: `change_id`, `timestamp_utc`, `reason` only

`gate`, `before_hash`, `after_hash`, `approved_by`, `rollback_ready` are now optional.
New optional fields: `impact` (enum: breaking/non_breaking/informational), `track` (string), `date` (date string).

---

## 3. New required fields

Five new top-level required fields:

### `mica_schema_version`
String, const `"0.1.8"`. Allows fast version detection without parsing `$id`.

### `invocation_protocol`
Declares how the archive reaches an AI session. Required fields: `primary_pattern`, `loading_order`.

```json
{
  "primary_pattern": "readme_protocol",
  "loading_order": ["memory/project.mica-lab.json", "memory/project.mica.json"],
  "readme_section_heading": "## [AI Session Protocol]",
  "fallback_patterns": ["global_skill"]
}
```

Patterns:
- `readme_protocol` — `[AI Session Protocol]` section in README (recommended default)
- `global_skill` — Agent Skills format, requires CLI installation
- `workspace_directive` — CLAUDE.md backstop
- `explicit` — user manually instructs AI to load MICA

See `MICA_INVOCATION_PATTERNS_v1.0.md` for full pattern specifications.

### `session_report_format`
Normative format for the session opening report. Required fields: `trigger`, `required_fields`, `gate_block_on`.

```json
{
  "trigger": "session_start",
  "required_fields": ["gate", "test_counts", "active_invariants", "track"],
  "gate_block_on": ["stage_gate_final==BLOCK"],
  "format_template": "[SESSION READY]\nGate: {gate} ({test_counts})\nTrack: {track}\nInvariants: {active_invariants}\nDeviations: {deviation_count}"
}
```

### `drift_response_policy`
Normalizes AI behavior on provenance hash mismatches.

```json
{
  "on_hash_mismatch": "warn_continue",
  "on_file_missing": "warn_block",
  "reminder_after_change": true,
  "inline_sync_required": true
}
```

`inline_sync_required: true` means the inline invariants table in README must be manually verified against `design_invariants` whenever the JSON is updated.

### `self_test_policy`
Runnable checks validating the archive against the real project. Distinct from `self_consistency_policy` (internal document consistency) — `self_test_policy` validates against the actual filesystem and project state.

```json
{
  "enabled": true,
  "run_on": ["session_start", "pre_commit"],
  "on_failure": "warn_continue",
  "checks": [
    {
      "id": "ST-001",
      "description": "All provenance_registry SHA256 values match ^[A-Fa-f0-9]{64}$",
      "check_type": "provenance_sha256_format",
      "severity": "error",
      "on_fail": "report_and_continue"
    },
    {
      "id": "ST-002",
      "description": "All registered files exist at their stated URIs",
      "check_type": "provenance_file_exists",
      "severity": "warning",
      "on_fail": "flag_as_drift"
    },
    {
      "id": "ST-003",
      "description": "invocation_protocol.primary_pattern is declared",
      "check_type": "invocation_pattern_present",
      "severity": "error",
      "on_fail": "require_acknowledgment"
    },
    {
      "id": "ST-004",
      "description": "All critical DIs appear in README [AI Session Protocol] inline invariants table",
      "check_type": "inline_invariants_match",
      "severity": "warning",
      "on_fail": "flag_as_drift"
    }
  ]
}
```

---

## 4. New optional fields

### `track_map`
Universal equivalent of MICA-LAB `track_decomposition`. Maps logical track IDs to files and applicable invariants. Optional — only add if the project uses track-based task routing.

```json
{
  "track_map": {
    "A": {
      "label": "Service Config & Clients",
      "description": "HTTP service configuration and client implementations",
      "files": ["pipeline/config.py", "pipeline/clients.py"],
      "invariants": ["DI-001", "DI-004"]
    },
    "B": {
      "label": "Data Adapters",
      "files": ["pipeline/adapters.py"],
      "invariants": ["DI-002", "DI-010"]
    }
  }
}
```

---

## 5. Additive changes to existing fields

### `collectorPipeline` — `pipeline_steps` (optional)
Structured step definitions alongside the existing `steps` string array.

```json
{
  "steps": ["collect", "normalize", "score", "dedup", "budget", "map", "handoff", "ledger"],
  "pipeline_steps": [
    {
      "name": "collect",
      "action": "Gather source files from provenance_registry and scope.include paths",
      "on_failure": "abort",
      "produces": ["raw_context_items"]
    }
  ]
}
```

### `operationMeta` — `invocation_notes` and `last_self_test_result` (optional)
```json
{
  "invocation_notes": "Primary invocation via README [AI Session Protocol]. Fallback: mica-context-loader skill.",
  "last_self_test_result": {
    "passed": true,
    "timestamp_utc": "2026-03-17T11:00:00Z",
    "failed_checks": []
  }
}
```

### `provenanceRecord` — `labels` (optional)
```json
{
  "uri": "README.md",
  "sha256": "39476c8f...",
  "kind": "file",
  "created_at": "2026-03-17T00:00:00Z",
  "trust_class": "canonical",
  "labels": ["primary_protocol", "session_anchor"]
}
```

---

## 6. Self-test vs Self-consistency

These two policies are distinct:

| Policy | What it checks | When |
|--------|---------------|------|
| `self_consistency_policy` | Internal document consistency (cross-field equalities, version matching, doc sanity) | Archive compile time |
| `self_test_policy` | Archive vs real world (file existence, hash integrity, README sync, pattern presence) | Session start, pre-commit |

Both are required in v0.1.8.

---

## 7. Scoring model

Unchanged from v0.1.7. Normative family: `weighted_sum_with_fail_closed_gates_v1`.

---

## 8. Selection rule

- `mica-lab-v0.1.5.schema.json` — laboratory-grade governance, parity contracts, cycle orchestration
- `mica-v0.1.8-universal.schema.json` — operational portability, invocation protocols, self-tests
- `mica-v0.1.7-universal.schema.json` — deprecated in favor of v0.1.8 (invocation problem unresolved)

---

## 9. Invocation patterns

See `MICA_INVOCATION_PATTERNS_v1.0.md` for complete specifications of:
- Pattern 1: README-as-Protocol (recommended default)
- Pattern 2: Global Skill (Agent Skills format)
- Pattern 3: Workspace Directive (CLAUDE.md)
- Comparison, selection guidance, full cascade flow

---

## 10. Expression Micro-Language (selfTestCheck.expression)

When selfTestCheck.expression is present, it must be evaluable by any conforming runtime.
The following closed vocabulary is normative. No other functions or operators are permitted.

### Path References (JSONPath subset)

| Syntax | Meaning |
|--------|---------|
| `$.field` | Top-level field |
| `$.field.subfield` | Nested field |
| `$.array[*].field` | All elements' field |
| `$.array[?severity==critical]` | Filter by equality |

### Permitted Functions (7 total)

| Function | Signature | Returns |
|----------|-----------|---------|
| `exists(path)` | JSONPath expression | boolean |
| `all(iterable, pred)` | array + predicate lambda | boolean |
| `any(iterable, pred)` | array + predicate lambda | boolean |
| `match(str, pattern)` | string + regex string | boolean |
| `len(iterable)` | array or string | integer |
| `contains(str, substr)` | string + string | boolean |
| `file_exists(uri)` | string URI | boolean -- AI session: read attempt; Python: os.path.exists |

### Lambda syntax (for all/any)

`all($.provenance_registry[*].sha256, match(x, '^[A-Fa-f0-9]{64}$'))`

The second argument to `all()`/`any()` is a predicate using `x` as the loop variable.

### Boolean operators

`and`, `or`, `not`, `==`, `!=`, `>=`, `<=`

### Examples

```
exists($.invocation_protocol.primary_pattern)
all($.provenance_registry[*].sha256, match(x, '^[A-Fa-f0-9]{64}$'))
all($.design_invariants[*].severity, contains('critical high medium low', x))
len($.provenance_registry) >= 1
file_exists($.provenance_registry[0].uri)
```

### Runtime implementation notes

- AI session: evaluate path references via read/glob; file_exists via read attempt
- Python: use `jsonpath-ng` for paths, `re` for match, `os.path.exists` for file_exists
- CI: same as Python
- Expression absence: check is human-only, no machine evaluation required

---

## 11. Adoption Profiles (Lite / Standard / Full)

Profiles are USAGE discipline, not schema validation tiers.
All profiles validate against the same mica-v0.1.8.1-universal.schema.json.
A "Lite" archive is schema-valid -- it just uses minimal values for complex policies.

### Lite -- Minimum viable context anchor

Focus: get MICA loading working. Useful for: onboarding, initial project setup, retrofitting.

Priority fields to fill meaningfully:
- `project` (all required subfields)
- `design_invariants` (at least 1 critical DI)
- `invocation_protocol` (primary_pattern + loading_order)
- `provenance_registry` (key files only)
- `session_report_format` (required_fields + gate_block_on)
- `drift_response_policy`
- `self_test_policy` (2-3 checks minimum)

Acceptable: copy scoring/budget/dedup/cache/ledger policies verbatim from minimal-instance.json.

### Standard -- Operational archive

Focus: project is actively maintained by AI sessions. Useful for: production projects, team onboarding.

Add to Lite:
- `track_map` (if project has 2+ logical file groups)
- `operation_meta.invocation_notes`
- `self_test_policy` with expression fields filled
- `deviation_log` entries as they occur
- Meaningful `semantic_validation_policy.rules`

### Full -- Governance-grade archive

Focus: audit trail, strict drift detection, team/multi-AI handoff. Useful for: regulated environments, long-lived projects.

Add to Standard:
- `self_consistency_policy` with custom doc_sanity_checks
- `operation_meta.last_self_test_result` updated after each session
- All `selfTestCheck.expression` fields filled
- `artifact_manifest` covering all canonical files
- `deviation_log` with rollback_ready entries for breaking changes
- `observability.slo_hints` tuned to project
- All `selfTestCheck.expression` fields filled

---

## 12. track_map -- Normative Usage Rules

### When to use track_map

Use track_map when ALL of the following are true:
1. Project has 2 or more logically distinct file groups
2. At least one design_invariant applies to only a subset of those groups
3. AI session tasks can be routed to a specific group (e.g. "change the adapter" -> Track B)

If track_map is absent, all design_invariants apply uniformly to all files.
This is the correct default for simple projects.

### Authority direction (single source of truth)

designInvariantEntry.track is the AUTHORITATIVE field.
trackEntry.invariants is DERIVED -- it must be populated from DI assignments, not edited directly.

Correct update flow:
1. Add/change `designInvariantEntry.track` to point to the relevant track ID
2. Recompute `trackEntry.invariants` by collecting all DI IDs with matching .track value
3. Never edit `trackEntry.invariants` directly

Divergence between trackEntry.invariants and DI assignments is a drift condition.
Detect with self_test check_type='track_map_files_registered'.

### Coupling track_map with self_test_policy

If track_map is present, self_test_policy MUST include at least one of:
- check_type: 'track_map_files_registered' (files in track_map appear in provenance_registry)
- check_type: 'inline_invariants_match' (critical DIs visible in README per-track section)

This is a usage discipline rule, not schema-enforced.

### Track ID naming

Track IDs are arbitrary strings. Recommendations:
- Single letter (A, B, C) for 5 or fewer tracks
- Descriptive slug (api, core, tests) for larger projects
- Avoid numeric IDs -- they imply ordering that may not exist
