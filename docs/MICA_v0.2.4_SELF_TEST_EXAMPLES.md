# MICA v0.2.4 self_test_policy — PCT-010 and PCT-011 Examples

`self_test_policy` blocks showing PCT-010 (binding completeness) and PCT-011 (lesson_ref existence) behavior.
These blocks extend the base PCT-001 through PCT-008 checks established in v0.2.2.

---

## Scenario A: All critical DIs bound (PCT-010 PASS)

Archive has critical DIs with `binding.origin_episode` set. PCT-010 passes.

```json
"self_test_policy": {
  "enabled": true,
  "run_on": ["session_start"],
  "on_failure": "warn_continue",
  "note": "v0.2.4 checks including binding completeness and lesson_ref validation.",
  "checks": [

    {
      "id": "PCT-001",
      "description": "mica.yaml composition contract exists",
      "check_type": "mica_yaml_present",
      "severity": "critical",
      "on_fail": "HALT: composition contract missing.",
      "expression": "file_exists('mica.yaml')"
    },

    {
      "id": "PCT-002",
      "description": "mica.yaml contains required fields",
      "check_type": "mica_yaml_fields_valid",
      "severity": "critical",
      "on_fail": "HALT: mica.yaml malformed.",
      "expression": "exists($.mica_spec) and exists($.mode) and len($.layers) >= 2"
    },

    {
      "id": "PCT-003",
      "description": "All required layer paths exist on disk",
      "check_type": "mica_yaml_paths_exist",
      "severity": "critical",
      "on_fail": "HALT: ghost path in mica.yaml.",
      "expression": "all($.layers[?(@.required != false)], file_exists($.path))"
    },

    {
      "id": "PCT-004",
      "description": "mode coherence: archive + playbook layers present",
      "check_type": "mica_yaml_mode_coherent",
      "severity": "error",
      "on_fail": "ACKNOWLEDGE: mode requires 'archive' and 'playbook' layers.",
      "expression": "any($.layers, $.name == 'archive') and any($.layers, $.name == 'playbook')"
    },

    {
      "id": "PCT-010",
      "description": "All critical design_invariants have binding.origin_episode",
      "check_type": "di_binding_completeness",
      "severity": "warning",
      "on_fail": "WARN: critical DIs missing binding.origin_episode. Escalates to FAIL when binding_required: true (planned v0.2.6).",
      "target": "archive design_invariants[severity==critical]",
      "expression": "all($.design_invariants[?(@.severity == 'critical')], exists($.binding.origin_episode))",
      "result": "PASS -- all 3 critical DIs have binding.origin_episode"
    },

    {
      "id": "PCT-011",
      "description": "All binding.lesson_ref paths exist on disk",
      "check_type": "lesson_ref_existence",
      "severity": "warning",
      "on_fail": "WARN: binding.lesson_ref dead link. A broken lesson_ref is worse than no lesson_ref.",
      "target": "archive design_invariants[].binding.lesson_ref",
      "expression": "all($.design_invariants[?(@.binding.lesson_ref)], file_exists($.binding.lesson_ref))",
      "result": "PASS -- all 2 lesson_ref paths exist"
    }

  ]
}
```

---

## Scenario B: Unbound critical DIs (PCT-010 WARN)

Archive has critical DIs without `binding`. Expected state for projects migrating from v0.2.3.

```json
"self_test_policy": {
  "enabled": true,
  "run_on": ["session_start"],
  "on_failure": "warn_continue",
  "note": "v0.2.4. PCT-010 WARN is expected -- binding.origin_episode not yet added to all critical DIs.",
  "checks": [

    {
      "id": "PCT-010",
      "description": "All critical design_invariants have binding.origin_episode",
      "check_type": "di_binding_completeness",
      "severity": "warning",
      "on_fail": "WARN: critical DIs missing binding.origin_episode: [DI-001, DI-003]. Add binding progressively as violations are observed. Escalates to FAIL when binding_required: true is set (planned v0.2.6).",
      "target": "archive design_invariants[severity==critical]",
      "expression": "all($.design_invariants[?(@.severity == 'critical')], exists($.binding.origin_episode))",
      "result": "WARN -- DI-001, DI-003 unbound"
    },

    {
      "id": "PCT-011",
      "description": "All binding.lesson_ref paths exist on disk",
      "check_type": "lesson_ref_existence",
      "severity": "warning",
      "on_fail": "WARN: binding.lesson_ref dead link.",
      "result": "INFO -- no lesson_ref fields declared; nothing to validate"
    }

  ]
}
```

CLOSED CONTRACT is preserved with PCT-010 WARN.

---

## Scenario C: Dead lesson_ref (PCT-011 WARN)

A `binding.lesson_ref` path is declared but does not exist on disk.

```json
{
  "id": "DI-002",
  "label": "billing-thresholds-are-measured",
  "severity": "critical",
  "binding": {
    "origin_episode": "EXP-023: lowering STABLE_THRESHOLD to 1 caused unstable chunks, savings dropped 40%",
    "violation_count": 1,
    "lesson_ref": "memory/lessons/2026-04-threshold-incident.md",
    "last_triggered": "2026-04-15"
  }
}
```

If `memory/lessons/2026-04-threshold-incident.md` does not exist:

```json
{
  "id": "PCT-011",
  "result": "WARN -- binding.lesson_ref dead links: [('DI-002', 'memory/lessons/2026-04-threshold-incident.md')]"
}
```

Fix: either create the lesson file or remove the `lesson_ref` field until the file exists.
A dead `lesson_ref` asserts evidence that cannot be read — it is worse than no reference.

---

## Scenario D: hook_output with violations_only filter

Archive DIs where some have `violation_count > 0` and others do not.

```json
"design_invariants": [
  {
    "id": "DI-001",
    "label": "no-whitespace-collapse-on-code",
    "severity": "critical",
    "binding": {
      "origin_episode": "EXP-017: re.sub collapse broke Python indentation",
      "violation_count": 2
    }
  },
  {
    "id": "DI-002",
    "label": "no-fss-optimized-marker",
    "severity": "critical",
    "binding": {
      "origin_episode": "EXP-019: marker caused double-optimization on re-run"
    }
  },
  {
    "id": "DI-003",
    "label": "chunk-cache-thresholds-are-tested",
    "severity": "critical",
    "statement": "STABLE_THRESHOLD=3 and CHUNK_CHARS=512 are verified constants.",
    "binding": {
      "origin_episode": "EXP-023: lowering threshold caused savings drop 40%",
      "violation_count": 1
    }
  }
]
```

With `hook_output: {di_filter: violations_only}`:

```text
[MICA] my-project v1.0.0 | mode=protocol_evolution | pattern=hook_trigger | DI=3crit | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): no-whitespace-collapse-on-code [2x]
[MICA:DI] DI-003(critical): chunk-cache-thresholds-are-tested [1x]
```

DI-002 is suppressed because `violation_count` is not set (treated as 0).

With `hook_output: {max_di_lines: 1, di_filter: violations_only}`:

```text
[MICA] my-project v1.0.0 | mode=protocol_evolution | pattern=hook_trigger | DI=3crit | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): no-whitespace-collapse-on-code [2x]
```

Only the first violation DI appears; cap of 1 reached.

---

## PCT-010 / PCT-011 Severity Decision Table

| Check | Severity | Affects CLOSED CONTRACT? |
|-------|----------|--------------------------|
| `PCT-010` binding completeness | `warning` | No — WARN is acceptable |
| `PCT-011` lesson_ref existence | `warning` | No — WARN is acceptable |
| Escalation trigger | `PCT-010` → `error` when `binding_required: true` | Yes — planned v0.2.6 |

CLOSED CONTRACT is defined by PCT-001, PCT-002, PCT-003, PCT-004, PCT-007, PCT-008 passing.
PCT-010 and PCT-011 are maturity indicators, not contract-breakers in v0.2.4.
