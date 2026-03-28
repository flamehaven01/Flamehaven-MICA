# v0.1.9 → v0.2.0 Migration Guide

## Overview

`v0.2.0` inherits the `mica.yaml` composition contract from `v0.1.9`.

The core question in `v0.2.0` is **not** whether a project has MICA packaging. That was closed in `v0.1.9`.

The new work in `v0.2.0` is whether optional profiles and draft layer extensions can be added **without breaking `v0.1.9` portability**.

Existing `v0.1.9` assets (`mica.yaml`, archive JSON, playbook, optional lessons/exemplars) are **preserved as-is** unless a project deliberately opts into a draft `v0.2.0` profile.

Rollback from draft `v0.2.0` exploration should mean removing only the draft profile additions, not rewriting the stable package.

```
Before (v0.1.9):
  my-project/
  ├── mica.yaml                        ← stable composition contract already present
  └── memory/
      ├── project.mica.v1.2.7.json
      ├── project-playbook.v1.2.7.md
      └── [optional lessons/ exemplars/]

After (v0.2.0):
  my-project/
  ├── mica.yaml                        ← preserved base contract
  └── memory/
      ├── project.mica.v1.2.7.json    ← preserved unless draft profile requires additive metadata
      ├── project-playbook.v1.2.7.md  ← preserved unless draft profile requires additive notes
      └── [optional draft profile artifacts]
```

---

## Migration Procedure

### Step 1: Confirm stable `v0.1.9` baseline

Before any `v0.2.0` draft work:

- confirm `mica.yaml` already exists
- confirm the package is readable as a stable `v0.1.9` package
- confirm draft work is additive and optional

If `mica.yaml` does not exist yet, do **not** start here. Migrate the project to `v0.1.9` first.

### Step 2: Determine mode

Determine the pattern in which the existing project is already using MICA.

| Existing Pattern | Mode to Select |
|---------|------------|
| Update archive after maintenance, preserve memory between sessions | `memory_injection` |
| Iterate dogfood experiments, accumulate lessons/exemplars | `protocol_evolution` |

**Decision Criteria:**
- If `lessons/` or `exemplars/` directories exist → `protocol_evolution`
- If experimental meta-documents like `MEMORY_LAYER_CONVENTIONS.md` exist → `protocol_evolution`
- If the pattern is pure maintenance + injection → `memory_injection`

### Step 3: Compose layers list

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

### Step 4: Determine draft scope

Choose whether the project is merely being version-aligned to the `0.2.0` branch, or whether it is opting into one or more draft profiles.

Recommended rule:

- no draft profile adoption yet → preserve all stable files as-is
- draft profile adoption → add only the smallest necessary additive metadata

### Step 5: Determine update_triggers

| mode | Recommended triggers |
|------|--------------|
| `memory_injection` | `on_maintenance_complete`, `on_explicit_save` |
| `protocol_evolution` | `on_dogfood_cycle_close`, `on_explicit_save` |

### Step 6: Update mica.yaml only if branch adoption is explicit

If a project explicitly enters the `v0.2.0` branch:

- update `mica_spec` to `0.2.0`
- keep the stable layer contract intact unless a draft profile adds optional fields

If a project remains on stable `v0.1.9`, do not touch `mica.yaml`.

### Step 7: Validate

Validate the created `mica.yaml` using the checklist below:

- [ ] `mica_spec: "0.2.0"` is declared
- [ ] `mode` is `memory_injection` or `protocol_evolution`
- [ ] Exactly 1 `archive` layer, `format: json`
- [ ] Exactly 1 `playbook` layer, `format: markdown`
- [ ] If `mode: protocol_evolution`, `lessons` layer is present
- [ ] All declared `path` files/directories actually exist on disk
- [ ] No fields outside the schema
- [ ] Any `v0.2.0` additions remain optional and do not break `v0.1.9` readability

---

## Rollback Procedure

```bash
# Remove only draft v0.2.0 additions.
# Do not delete the stable v0.1.9 package unless intentionally rolling back to pre-MICA state.
```

---

## Example Branch Adoption: flamehaven-space

**Before (v0.1.9 stable):**
```
flamehaven-space/
├── mica.yaml
└── memory/
    ├── flamehaven-space-maintainer.mica.v1.2.7.json   ← archive
    └── flamehaven-space-maintainer-playbook.v1.2.7.md  ← playbook
```

**After (v0.2.0 draft branch adoption):**
```
flamehaven-space/
├── mica.yaml                                            ← branch version may be updated intentionally
└── memory/
    ├── flamehaven-space-maintainer.mica.v1.2.7.json     ← preserved unless additive profile metadata is introduced
    └── flamehaven-space-maintainer-playbook.v1.2.7.md   ← preserved unless additive draft notes are introduced
```

Decision rationale:
- No `lessons/` → `mode: memory_injection`
- Confirmed maintenance + injection pattern → `on_maintenance_complete` trigger

---

## Example Branch Adoption: CareChainGovernanceEngine

**Before (v0.1.9 stable):**
```
CareChainGovernanceEngine/
├── mica.yaml
└── memory/
    ├── CCGE_TARGET_MICA_ARCHIVE_BASELINE.json          ← archive
    ├── MICA_CCGE_STEM_T3_PLAYBOOK.md                   ← playbook
    ├── MEMORY_LAYER_CONVENTIONS.md                     ← meta
    ├── CCGE_TARGET_MAINTAINER_PLAYBOOK_BASELINE.md     ← meta
    ├── lessons/                                        ← 4 files
    └── exemplars/                                      ← exemplars
```

**After (v0.2.0 draft branch adoption):**
```
CareChainGovernanceEngine/
├── mica.yaml                                           ← branch version may be updated intentionally
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

## v0.2.0 Archive Schema Alignment

### Overview

One draft branch concern in `v0.2.0` is whether archive JSON should stay aligned with the same version axis as `mica.yaml`.

This is an additive alignment question, not the introduction of MICA packaging itself.

```
Before (v0.1.8.1):
  mica.yaml    → mica_spec: "0.2.0"     (version declaration)
  archive.json → (no mica_spec)         ← machine cannot verify the connection

After (v0.2.0 aligned):
  mica.yaml    → mica_spec: "0.2.0"
  archive.json → mica_spec: "0.2.0"    ← machine-readable version alignment
```

### Two Fields to Add to archive JSON

```json
{
  "mica_spec": "0.2.0",
  "mica_schema_version": "0.2.0",
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

Apply the decision procedure from `mica-v0.2.0-archive-changes.schema.json`:

1. Does the archive have a `mica_spec` field? → No → **COMPAT-001** (legacy-valid, add on next version bump)
2. Does `mica_spec` match `mica.yaml mica_spec`? → Yes → **COMPAT-003** (aligned)
3. Does `mica_spec` mismatch? → **COMPAT-002** (drift-warning, sync on next version bump)
4. Is `mica_schema_version: "baseline-draft"`? → **COMPAT-004** (template-valid, apply at instantiation)

Each artifact lands in exactly one COMPAT rule based on its own state. No cross-project tracking belongs here.

### flamehaven-space Application Example

```json
{
  "mica_spec": "0.2.0",
  "mica_schema_version": "0.2.0",
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

See `0.2.0/mica-v0.2.0-archive-changes.schema.json`.  
The 4 compatibility rules (COMPAT-001~004) and the COMPAT decision procedure are documented there.

