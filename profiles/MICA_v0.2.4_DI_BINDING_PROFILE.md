# MICA v0.2.4 — DI Binding Profile

## Purpose

DI binding grounds critical design invariants in the episodes that created them.
This profile defines how to author `binding` blocks correctly, when to add them,
and how PCT-010 and PCT-011 validate them.

---

## What binding is for

A design invariant without binding is a rule. A design invariant with binding is evidence.

The distinction matters when a guard fires:

Without binding:
```text
[GUARD] DI-001 no-destructive-reset: about to run git reset --hard
Proceed? This requires explicit acknowledgment.
```

With binding:
```text
[GUARD] DI-001 no-destructive-reset: about to run git reset --hard
Evidence: EXP-017: force-reset deleted uncommitted work [2x violated]
Proceed? This requires explicit acknowledgment.
```

Binding gives the AI the WHY, not just the rule. Surface it when a guard fires.

---

## Authoring Rules

### Rule 1: Add binding progressively, not speculatively

Do not create `binding` blocks before a real episode exists.
An invented `origin_episode` is noise — it provides no actual grounding.

Timeline:
1. Start a new DI with no `binding` block (PCT-010 will WARN — acceptable)
2. When a violation occurs, add `binding.origin_episode` describing the incident
3. When a lesson file is written, add `lesson_ref` pointing to it
4. Update `violation_count` and `last_triggered` as violations accumulate

### Rule 2: origin_episode must name the incident

Not acceptable:
```json
"origin_episode": "discovered during review"
```

Acceptable:
```json
"origin_episode": "EXP-017: re.sub collapse broke Python indentation, CI failed on 3 modules"
```

The episode must name the specific incident, not just describe the rule. Minimum 10 characters.
Include: experiment or event ID, what went wrong, when or where it was observed.

### Rule 3: lesson_ref must point to an existing file

If you declare `lesson_ref`, the file must exist on disk before PCT-011 runs.

```json
"lesson_ref": "memory/lessons/2026-04-whitespace-incident.md"
```

A dead `lesson_ref` is worse than no `lesson_ref`. It asserts evidence that cannot be read.

If the lesson file does not exist yet, omit `lesson_ref` until it does.

### Rule 4: violation_count must be updated manually

`violation_count` is not auto-incremented. Update it when a new violation is logged.

```json
"violation_count": 2
```

`di_filter: violations_only` in hook output uses this field.
DIs with no `violation_count` (or `violation_count: 0`) are suppressed under that filter.

### Rule 5: last_triggered is ISO date only

```json
"last_triggered": "2026-04-07"
```

Pattern: `YYYY-MM-DD`. No timestamps, no relative dates.

---

## Binding Block Structure

```json
{
  "id": "DI-001",
  "label": "no-whitespace-collapse-on-code",
  "statement": "Never apply re.sub(r'\\s+', ' ') to content containing code.",
  "severity": "critical",
  "binding": {
    "origin_episode": "EXP-017: re.sub collapse broke Python indentation, CI failed on 3 modules",
    "violation_count": 2,
    "lesson_ref": "memory/lessons/2026-04-whitespace-incident.md",
    "last_triggered": "2026-04-07"
  }
}
```

Only `origin_episode` is required. Other fields are optional.

---

## PCT-010: Binding Completeness

PCT-010 checks whether critical DIs have `binding.origin_episode`.

| State | PCT-010 result |
|-------|---------------|
| All critical DIs bound | PASS |
| One or more critical DIs unbound | WARN (names the unbound DI IDs) |
| `binding_required: true` set in mica.yaml (planned v0.2.6) | FAIL |

WARN does not break CLOSED CONTRACT status.

Maturity path:
- v0.2.3–v0.2.5: WARN only
- v0.2.6+: FAIL when `binding_required: true`
- v0.3.0: global FAIL reviewed

---

## PCT-011: lesson_ref Existence

PCT-011 checks whether declared `binding.lesson_ref` paths exist on disk.

| State | PCT-011 result |
|-------|---------------|
| Dead link found | WARN — names the broken paths |
| All declared paths exist | PASS |
| No `lesson_ref` fields declared | INFO — nothing to validate |

WARN does not break CLOSED CONTRACT status.

---

## Domain Boundary

`binding` in archive `design_invariants` is governed by:
`mica-v0.2.4-archive-di-binding.schema.json`

`binding` in `mica.yaml drift_profile.classes[]` is governed by:
`mica.yaml.schema.json/$defs/driftClass`

These are different objects. Do not use the archive schema for mica.yaml DI classes
or vice versa. See `$comment` in the archive schema for the authoritative domain separation note.

---

## Backward Compatibility

Archives without `binding` blocks are fully valid. PCT-010 warns but does not fail.
The `allOf` composition in `designInvariantEntryV024` does not apply `additionalProperties: false`
at the combined level, so legacy fields (`rationale`, `track`, `note`) in pre-v0.2.3 archives
pass validation without modification.

DIs with `rationale` (pre-v0.2.3 style) are accepted. Add `binding` progressively — do not
replace `rationale` with `binding.origin_episode` in the same edit unless you have verified
the content maps correctly.
