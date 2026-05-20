# mica.yaml — MICA Composition Contract Specification v0.2.4

## Purpose

`mica.yaml` is the **composition contract** for a MICA package.
When this file exists, it declares unambiguously: "this project's MICA consists of these files."

**Design principles:**
- Schema = Spec = Example = Validator. Four-surface alignment.
- `additionalProperties: false` applied throughout.
- MICA is a Memory Layer specialist, not an agent OS.

---

## Placement Contexts

| File present | `mica.yaml` location | playbook location |
|---|---|---|
| `agent.yaml` or `AGENTS.md` | `memory/mica.yaml` | `workflows/` recommended |
| `SKILL.md` | `memory/mica.yaml` | `memory/` or `spec/` |
| None (standalone) | `mica.yaml` (root) | `memory/` |

---

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `mica_spec` | `string` | Spec version. Pattern: `X.Y.Z`. Use `"0.2.4"`. |
| `mode` | `enum` | `memory_injection` or `protocol_evolution` |
| `layers` | `array` | Package files. `archive` + `playbook` required. |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Package ID. Kebab-case. |
| `description` | `string` | Human-readable memo. Max 300 chars. |
| `invocation_protocol` | `object` | How MICA is invoked. See below. |
| `update_triggers` | `array` | When archive should be updated. |
| `archive_policy` | `object` | Rotation and retention policy. |
| `drift_profile` | `object` | mica.yaml DI governance (see `driftClass`). |

---

## mode

| Value | Meaning |
|-------|---------|
| `memory_injection` | Post-maintenance memory carryover |
| `protocol_evolution` | Iterative protocol growth with lessons accumulation |

---

## layers

### Layer Object Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | `string` | Layer ID (standard names below) |
| `path` | Yes | `string` | Relative to project root |
| `format` | Yes | `enum` | `json` or `markdown` |
| `required` | No | `boolean` | Default: `true` |
| `max_lines` | No | `integer` | Line count limit |
| `loading_hint` | No | `enum` | `always` / `on_demand` / `session_start_only` / `hook` |

### Standard Layer Names

| name | Required | Description |
|------|----------|-------------|
| `archive` | **Yes** | MICA JSON archive |
| `playbook` | **Yes** | Markdown playbook |
| `lessons` | Recommended for `protocol_evolution` | Dogfood cycle records |
| `working_memory` | No | Live inter-session state |
| `exemplars` | No | Success/failure case collection |

---

## invocation_protocol

```yaml
invocation_protocol:
  primary_pattern: hook_trigger        # see pattern table below
  hook_script: core/my_hook.py        # required when hook_trigger
  hook_output_prefix: "[MICA]"        # optional prefix
  hook_output:                         # v0.2.4: volume control
    max_di_lines: 3                    # cap [MICA:DI] lines (0 = unlimited)
    di_filter: violations_only         # all | violations_only
```

### primary_pattern values

| Pattern | Use when |
|---------|----------|
| `readme_protocol` | Broad portability, no hook surface |
| `hook_trigger` | Pre-prompt hook exists and is maintained |
| `agent_yaml_bootstrap` | Agent OS project (`agent.yaml` present) |
| `global_skill` | Skill-driven environment |
| `workspace_directive` | Lightweight workspace binding |
| `explicit` | Manual invocation only |

### hook_output (v0.2.4)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_di_lines` | `integer` | unlimited | Cap on `[MICA:DI]` lines emitted |
| `di_filter` | `enum` | `all` | `violations_only` suppresses DIs with `violation_count == 0` |

When `hook_trigger` is used with many critical DIs, set `hook_output` to avoid
polluting hook context with low-signal invariants.

---

## update_triggers

| Value | Mode | Meaning |
|-------|------|---------|
| `on_maintenance_complete` | `memory_injection` | After a maintenance task |
| `on_dogfood_cycle_close` | `protocol_evolution` | After a dogfood cycle |
| `on_explicit_save` | Both | Explicit save request |
| `on_version_bump` | Both | Version number incremented |
| `on_hook_trigger` | Both | Hook fires (useful for lightweight archives) |

---

## archive_policy

| Field | Allowed values | Description |
|-------|----------------|-------------|
| `rotation` | `on_version_bump` / `monthly` / `quarterly` | When prior archives rotate |
| `retention` | `indefinite` / `7y` / `90d` etc. | `indefinite` recommended |

---

## Validation Rules

A `mica.yaml` is valid when:

1. `mica_spec` matches `X.Y.Z`
2. `mode` is `memory_injection` or `protocol_evolution`
3. `layers` has exactly one `archive` (json) and one `playbook` (markdown)
4. All `required: true` layer paths exist on disk
5. All fields are defined in this spec
6. If `primary_pattern: hook_trigger`, then `hook_script` is present and the script exists
7. If `primary_pattern: protocol_evolution`, a `lessons` layer is present

---

## DI Binding in Archive (v0.2.4)

DI binding belongs in the archive `design_invariants`, not in `mica.yaml`.

The `drift_profile.classes[].binding` field in this contract governs mica.yaml DI classes.
For archive DI binding, use `mica-v0.2.4-archive-di-binding.schema.json`.

Archive DI binding structure:

```json
{
  "id": "DI-001",
  "label": "no-whitespace-collapse-on-code",
  "statement": "...",
  "severity": "critical",
  "binding": {
    "origin_episode": "EXP-017: re.sub collapsed indentation, CI failed 2026-04-07",
    "violation_count": 2,
    "lesson_ref": "memory/lessons/2026-04-whitespace-incident.md",
    "last_triggered": "2026-04-07"
  }
}
```

`origin_episode` is required (minLength: 10). Other fields are optional.
`lesson_ref` is validated by PCT-011 for file existence.
