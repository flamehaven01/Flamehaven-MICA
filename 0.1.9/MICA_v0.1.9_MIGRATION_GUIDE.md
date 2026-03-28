# v0.1.8.1 → v0.1.9 Migration Guide

## Overview

The core change in v0.1.9 is the **introduction of the `mica.yaml` composition contract**.

Existing v0.1.8.1 assets (archive JSON, playbook.md) are **preserved as-is**. `mica.yaml` merely adds a declaration layer on top of existing files. Rollback is complete by deleting the single `mica.yaml` file.

```
Before (v0.1.8.1):
  my-project/
  └── memory/
      ├── project.mica.v1.2.7.json    ← this was the entirety of MICA
      └── project-playbook.v1.2.7.md

After (v0.1.9):
  my-project/
  ├── mica.yaml                        ← new (composition contract)
  └── memory/
      ├── project.mica.v1.2.7.json    ← preserved, no changes
      └── project-playbook.v1.2.7.md  ← preserved, no changes
```

---

## Migration Procedure

### Step 1: Determine mode

Determine the pattern in which the existing project was using MICA.

| Existing Pattern | Mode to Select |
|---------|------------|
| Update archive after maintenance, preserve memory between sessions | `memory_injection` |
| Iterate dogfood experiments, accumulate lessons/exemplars | `protocol_evolution` |

**Decision Criteria:**
- If `lessons/` or `exemplars/` directories exist → `protocol_evolution`
- If experimental meta-documents like `MEMORY_LAYER_CONVENTIONS.md` exist → `protocol_evolution`
- If the pattern is pure maintenance + injection → `memory_injection`

### Step 2: Compose layers list

Enumerate current MICA-related files by traversing the `memory/` directory.

```
Required mappings:
  *.mica.*.json           → name: archive,   format: json
  *playbook*.md           → name: playbook,  format: markdown

Optional mappings (add if present):
  MEMORY.md or context.md   → name: working_memory, format: markdown
  lessons/                  → name: lessons,         format: markdown
  exemplars/                → name: exemplars,       format: markdown
```

### Step 3: Determine update_triggers

| mode | Recommended triggers |
|------|--------------|
| `memory_injection` | `on_maintenance_complete`, `on_explicit_save` |
| `protocol_evolution` | `on_dogfood_cycle_close`, `on_explicit_save` |

### Step 4: Create mica.yaml

Create a new `mica.yaml` at the project root.  
**Do not modify existing files under any circumstances.**

### Step 5: Validate

Validate the created `mica.yaml` using the checklist below:

- [ ] `mica_spec: "0.1.9"` is declared
- [ ] `mode` is `memory_injection` or `protocol_evolution`
- [ ] Exactly 1 `archive` layer, `format: json`
- [ ] Exactly 1 `playbook` layer, `format: markdown`
- [ ] If `mode: protocol_evolution`, `lessons` layer is present
- [ ] All declared `path` files/directories actually exist on disk
- [ ] No fields outside the schema

---

## Rollback Procedure

```bash
# Deleting only mica.yaml fully reverts to v0.1.8.1 state
# No changes are made to existing archive JSON and playbook files
rm mica.yaml
```

---

## Example Migration: flamehaven-space

**Before (v0.1.8.1):**
```
flamehaven-space/
└── memory/
    ├── flamehaven-space-maintainer.mica.v1.2.7.json   ← archive
    └── flamehaven-space-maintainer-playbook.v1.2.7.md  ← playbook
```

**After (v0.1.9):**
```
flamehaven-space/
├── mica.yaml                                            ← new
└── memory/
    ├── flamehaven-space-maintainer.mica.v1.2.7.json   ← preserved
    └── flamehaven-space-maintainer-playbook.v1.2.7.md  ← preserved
```

Decision rationale:
- No `lessons/` → `mode: memory_injection`
- Confirmed maintenance + injection pattern → `on_maintenance_complete` trigger

---

## Example Migration: CareChainGovernanceEngine

**Before (v0.1.8.1):**
```
CareChainGovernanceEngine/
└── memory/
    ├── CCGE_TARGET_MICA_ARCHIVE_BASELINE.json          ← archive
    ├── MICA_CCGE_STEM_T3_PLAYBOOK.md                   ← playbook
    ├── MEMORY_LAYER_CONVENTIONS.md                     ← meta
    ├── CCGE_TARGET_MAINTAINER_PLAYBOOK_BASELINE.md     ← meta
    ├── lessons/                                        ← 4 files
    └── exemplars/                                      ← exemplars
```

**After (v0.1.9):**
```
CareChainGovernanceEngine/
├── mica.yaml                                           ← new
└── memory/
    ├── CCGE_TARGET_MICA_ARCHIVE_BASELINE.json          ← preserved
    ├── MICA_CCGE_STEM_T3_PLAYBOOK.md                   ← preserved
    ├── MEMORY_LAYER_CONVENTIONS.md                     ← preserved
    ├── CCGE_TARGET_MAINTAINER_PLAYBOOK_BASELINE.md     ← preserved
    ├── lessons/                                        ← preserved
    └── exemplars/                                      ← preserved
```

Decision rationale:
- `lessons/` present + `MEMORY_LAYER_CONVENTIONS.md` present → `mode: protocol_evolution`
- Confirmed dogfood cycle pattern → `on_dogfood_cycle_close` trigger
- `exemplars/` present but experimental → `required: false`

---

## v0.1.9 Archive Schema Alignment

### Overview

The second change in v0.1.9 is adding the `mica_spec` field to the archive JSON.  
This change places `mica.yaml` and archive JSON **on the same version axis**.

```
Before (v0.1.8.1):
  mica.yaml    → mica_spec: "0.1.9"     (version declaration)
  archive.json → (no mica_spec)         ← machine cannot verify the connection

After (v0.1.9 aligned):
  mica.yaml    → mica_spec: "0.1.9"
  archive.json → mica_spec: "0.1.9"    ← machine-readable version alignment
```

### Two Fields to Add to archive JSON

```json
{
  "mica_spec": "0.1.9",
  "mica_schema_version": "0.1.9",
  ...all existing fields preserved as-is...
}
```

**`mica_spec`**: must match the composition contract version in mica.yaml  
**`mica_schema_version`**: archive JSON schema version (existing field, value updated only)

### When to Apply

**Do not modify existing files right now.**  
Add them naturally at the following points:

| mode | When to Apply |
|------|---------|
| `memory_injection` | On next archive injection after maintenance |
| `protocol_evolution` | On next dogfood cycle closeout |

### Compatibility Rules

| Status | Verdict | Action |
|------|------|------|
| archive has no `mica_spec` | **legacy-valid** (COMPAT-001) | Add on next version bump |
| `mica_spec` present and matches `mica.yaml` | **aligned** (COMPAT-003) | Full machine-readable contract |
| `mica_spec` present but does not match `mica.yaml` | **drift-warning** (COMPAT-002) | Sync on next version bump |
| `mica_schema_version: "baseline-draft"` | **template-valid** (COMPAT-004) | Apply at instantiation time |

### How to Determine Your Archive's COMPAT Rule

Apply the decision procedure from `mica-v0.1.9-archive-changes.schema.json`:

1. Does the archive have a `mica_spec` field? → No → **COMPAT-001** (legacy-valid, add on next version bump)
2. Does `mica_spec` match `mica.yaml mica_spec`? → Yes → **COMPAT-003** (aligned)
3. Does `mica_spec` mismatch? → **COMPAT-002** (drift-warning, sync on next version bump)
4. Is `mica_schema_version: "baseline-draft"`? → **COMPAT-004** (template-valid, apply at instantiation)

Each artifact lands in exactly one COMPAT rule based on its own state. No cross-project tracking belongs here.

### flamehaven-space Application Example

```json
{
  "mica_spec": "0.1.9",
  "mica_schema_version": "0.1.9",
  "project": {
    "name": "flamehaven-space",
    "full_name": "Flamehaven.space B2B AI Systems Site",
    "version": "1.2.8",
    ...
  },
  ...all existing fields preserved...
}
```

### Detailed Schema Change Specification

See `0.1.9/mica-v0.1.9-archive-changes.schema.json`.  
The 4 compatibility rules (COMPAT-001~004) and the COMPAT decision procedure are documented there.
