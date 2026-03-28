# mica.yaml — MICA Composition Contract Specification v0.1.9

## Purpose

`mica.yaml` is the **composition contract** for a MICA package.

When this file exists, it unambiguously declares: "this project's MICA consists of these files."
This resolves the fundamental design gap of prior versions — *the absence of an external standard for determining what a MICA package is*.

**Design principles:**
- Schema = Spec = Example = Validator. Four-surface alignment. No surface leads or lags another.
- `additionalProperties: false` applied throughout. Undocumented fields do not exist.
- MICA is a Memory Layer specialist. It does not model itself on an agent OS.

---

## Placement Contexts

`mica.yaml` placement is determined by project type. Three contexts exist.

---

### Context 1: Standalone Project (default)

A project with no `agent.yaml` and no `SKILL.md`. `mica.yaml` is the sole root manifest.

```
my-project/
├── mica.yaml                  <- at root (owner)
├── README.md
└── memory/
    ├── project.mica.v1.2.7.json
    └── project-playbook.v1.2.7.md
```

---

### Context 2: Agent OS Project

A project that has `agent.yaml` or `AGENTS.md`. The agent manifest owns the root, so `mica.yaml` moves inside `memory/`. The playbook moves to `workflows/`.

```
my-agent/
├── agent.yaml                 <- Agent OS manifest (root owner)
├── SOUL.md
├── RULES.md
├── memory/
│   ├── mica.yaml              <- inside memory/ (Memory Layer)
│   └── project.mica.v1.0.0.json
└── workflows/
    └── project-playbook.v1.0.0.md
```

`layers[].path` values are relative to the project root:

```yaml
layers:
  - name: archive
    path: memory/project.mica.v1.0.0.json
  - name: playbook
    path: workflows/project-playbook.v1.0.0.md
```

**Invocation in Context 2:**  
Use `primary_pattern: agent_yaml_bootstrap`. Add a MICA loading directive to `agent.yaml`'s `instructions` block:

```yaml
# agent.yaml (excerpt)
instructions:
  - "Before any work: load memory/mica.yaml to initialize the MICA memory layer."
  - "Follow the invocation sequence in memory/mica.yaml and the archive at its declared path."
```

The archive's `invocation_protocol.primary_pattern` must be set to `"agent_yaml_bootstrap"`.  
MICA remains the Memory Layer. Agent OS owns execution context, tools, and capabilities.

---

### Context 3: Skill Project

A project where `SKILL.md` is the entry point (Claude Skills / agent skills standard).
MICA invocation is declared inside `SKILL.md`'s `## Instructions` section.
`mica.yaml` is placed in `memory/`.

```
my-skill/
├── SKILL.md                   <- entry point (first file AI reads)
│   └── ## Instructions
│       └── "1. Load memory/mica.yaml to initialize memory layer"
├── spec/
├── templates/
└── memory/
    ├── mica.yaml              <- inside memory/
    └── skill.mica.v1.0.0.json
```

---

### Placement Decision Rule

| File present in project | `mica.yaml` location | playbook location |
|-------------------------|---------------------|-------------------|
| `agent.yaml` or `AGENTS.md` | `memory/mica.yaml` | `workflows/` recommended |
| `SKILL.md` | `memory/mica.yaml` | `memory/` or `spec/` |
| None of the above (standalone) | `mica.yaml` (root) | `memory/` |

**Core principle:** MICA is a Memory Layer. When another system (agent.yaml, SKILL.md) owns the root, MICA moves into `memory/`.

---

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `mica_spec` | `string` | Spec version this mica.yaml targets. Pattern: `X.Y.Z` |
| `mode` | `enum` | Operational mode: `memory_injection` or `protocol_evolution` |
| `layers` | `array` | List of files composing this MICA package. `archive` + `playbook` layers required. |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | MICA package identifier. Kebab-case recommended. |
| `update_triggers` | `array` | Conditions under which the archive should be updated. |
| `archive_policy` | `object` | Version rotation and retention policy. |
| `description` | `string` | Human-readable memo. Max 300 chars. |

---

## mode

```yaml
mode: memory_injection
```

| Value | Meaning | Core Pattern |
|-------|---------|-------------|
| `memory_injection` | Compensates for AI session amnesia by injecting post-maintenance learnings into the archive | Maintenance done → archive updated → next AI session reads it |
| `protocol_evolution` | MICA and playbook evolve together through dogfood cycles | Cycle closes → lessons accumulate → archive updated → next cycle improves |

---

## layers

Declares the files that compose this MICA package.

**Constraints:**
- Minimum 2 layers required.
- Exactly one layer with `name: archive` and `format: json` must exist.
- Exactly one layer with `name: playbook` and `format: markdown` must exist.
- For `mode: protocol_evolution`, a `name: lessons` layer is strongly recommended.

### Layer Object Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | `string` | Layer identifier. Use standard names below. |
| `path` | Yes | `string` | Path relative to project root. |
| `format` | Yes | `enum` | `json` or `markdown` |
| `required` | No | `boolean` | Whether the file must exist. Default: `true` |
| `max_lines` | No | `integer` | Maximum line count for the layer. Useful for `working_memory`. |
| `loading_hint` | No | `enum` | AI loading hint: `always` \| `on_demand` \| `session_start_only` |

### Standard Layer Names

| name | Description | Required |
|------|-------------|----------|
| `archive` | MICA JSON archive. Single source of operational truth. | **Required** |
| `playbook` | Markdown playbook. Procedures and context. | **Required** |
| `working_memory` | Live inter-session state. Line count limit recommended. | Optional |
| `lessons` | Dogfood cycle learning records directory. | Recommended for `protocol_evolution` |
| `exemplars` | Success and failure case collection directory. | Optional |

---

## update_triggers

Declares when the MICA archive should be updated.

| Value | Appropriate mode | Meaning |
|-------|-----------------|---------|
| `on_maintenance_complete` | `memory_injection` | After a maintenance task completes |
| `on_dogfood_cycle_close` | `protocol_evolution` | After a dogfood cycle closes |
| `on_explicit_save` | Both | When AI or operator explicitly requests save |
| `on_version_bump` | Both | When the MICA version number is incremented |

---

## archive_policy

| Field | Type | Allowed values | Description |
|-------|------|----------------|-------------|
| `rotation` | `enum` | `on_version_bump` \| `monthly` \| `quarterly` | When prior archives are moved to history |
| `retention` | `string` | `indefinite` \| `7y` \| `90d` etc. | Retention period. `indefinite` recommended — MICA is institutional memory. |

---

## Validation Rules

A `mica.yaml` is valid when all of the following are satisfied:

1. `mica_spec` matches pattern `X.Y.Z`
2. `mode` is `memory_injection` or `protocol_evolution`
3. `layers` contains exactly one `name: archive`, `format: json` layer
4. `layers` contains exactly one `name: playbook`, `format: markdown` layer
5. All `layers[].required: true` files exist on disk
6. All declared fields are defined in this spec (undeclared fields are rejected)
7. All `update_triggers` values are within the allowed enum
