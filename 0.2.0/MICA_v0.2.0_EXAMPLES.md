# mica.yaml Examples v0.2.0

Standard examples for the two operating modes.
All fields in this file are defined in mica.yaml.schema.json.

---

## Example A: memory_injection mode

```yaml
# mica.yaml
# flamehaven-space maintenance agent
# Pattern: update archive after maintenance completion → read by next AI session

mica_spec: "0.2.0"
name: flamehaven-space-maintainer
mode: memory_injection
description: "Session memory layer for the Next.js B2B site maintenance agent"

layers:
  - name: archive
    path: memory/flamehaven-space-maintainer.mica.v1.2.7.json
    format: json
    loading_hint: always

  - name: playbook
    path: memory/flamehaven-space-maintainer-playbook.v1.2.7.md
    format: markdown
    loading_hint: always

update_triggers:
  - on_maintenance_complete
  - on_explicit_save

archive_policy:
  rotation: on_version_bump
  retention: indefinite
```

**Characteristics of this example:**
- Minimal configuration: only 2 layers declared — archive + playbook
- `on_maintenance_complete`: injection trigger on maintenance completion
- No `working_memory` layer: in this pattern, archive is the single source of truth
- `retention: indefinite`: site history becomes institutional memory

---

## Example B: protocol_evolution mode

```yaml
# mica.yaml
# CCGE STEM-T3 protocol evolution agent
# Pattern: dogfood cycle → accumulate lessons → update archive → next cycle

mica_spec: "0.2.0"
name: ccge-stem-t3
mode: protocol_evolution
description: "Memory layer for CareChainGovernanceEngine MICA+STEM-AI integration experiments"

layers:
  - name: archive
    path: memory/CCGE_TARGET_MICA_ARCHIVE_BASELINE.json
    format: json
    loading_hint: always

  - name: playbook
    path: memory/MICA_CCGE_STEM_T3_PLAYBOOK.md
    format: markdown
    loading_hint: always

  - name: lessons
    path: memory/lessons/
    format: markdown
    loading_hint: on_demand

  - name: exemplars
    path: memory/exemplars/
    format: markdown
    required: false
    loading_hint: on_demand

update_triggers:
  - on_dogfood_cycle_close
  - on_explicit_save

archive_policy:
  rotation: on_version_bump
  retention: indefinite
```

**Characteristics of this example:**
- Extended configuration: 4 layers — archive + playbook + lessons + exemplars
- `required: false` on `exemplars` layer: valid even in early stages before exemplars are created
- `on_dogfood_cycle_close`: trigger on cycle close
- `loading_hint: on_demand`: lessons/exemplars loaded only when needed, conserving tokens

---

## Validation Checklist

Both examples satisfy the following:

| Validation Rule | Example A | Example B |
|----------|-----------|-----------|
| `mica_spec` pattern X.Y.Z | ✓ "0.2.0" | ✓ "0.2.0" |
| `mode` allowed value | ✓ memory_injection | ✓ protocol_evolution |
| `archive` layer present | ✓ | ✓ |
| `playbook` layer present | ✓ | ✓ |
| `lessons` layer (recommended for protocol_evolution) | N/A | ✓ |
| All fields exist in schema | ✓ | ✓ |
| `update_triggers` uses only allowed enum values | ✓ | ✓ |
| No undeclared fields | ✓ | ✓ |

