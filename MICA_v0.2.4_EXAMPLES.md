# mica.yaml Examples v0.2.4

Canonical examples for the recommended operating configurations.
v0.2.4 additions: DI binding in archive, `hook_output` policy in mica.yaml.

---

## Example A — memory_injection + readme_protocol

```yaml
mica_spec: "0.2.4"
name: flamehaven-space-maintainer
mode: memory_injection
description: "Session memory layer for a Next.js B2B site maintainer"

layers:
  - name: archive
    path: memory/flamehaven-space-maintainer.mica.v1.2.10.json
    format: json
    loading_hint: always

  - name: playbook
    path: memory/flamehaven-space-maintainer-playbook.v1.2.10.md
    format: markdown
    loading_hint: always

invocation_protocol:
  primary_pattern: readme_protocol

update_triggers:
  - on_maintenance_complete
  - on_explicit_save

archive_policy:
  rotation: on_version_bump
  retention: indefinite
```

Use when broad portability matters more than hard runtime guarantees.

---

## Example B — protocol_evolution + readme_protocol

```yaml
mica_spec: "0.2.4"
name: ccge-stem-t3
mode: protocol_evolution
description: "Protocol memory layer for iterative governance experiments"

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

invocation_protocol:
  primary_pattern: readme_protocol

update_triggers:
  - on_dogfood_cycle_close
  - on_explicit_save

archive_policy:
  rotation: on_version_bump
  retention: indefinite
```

Use when lessons accumulation matters more than per-prompt enforcement.

---

## Example C — protocol_evolution + hook_trigger + hook_output (v0.2.4)

```yaml
mica_spec: "0.2.4"
name: flamehaven-super-saver
mode: protocol_evolution
description: "Token-saving middleware with hook-guaranteed MICA activation"

layers:
  - name: archive
    path: memory/flamehaven-super-saver.mica.v1.0.0.json
    format: json
    loading_hint: hook

  - name: playbook
    path: memory/flamehaven-super-saver-playbook.v1.0.0.md
    format: markdown
    loading_hint: always

  - name: lessons
    path: memory/lessons/
    format: markdown
    loading_hint: on_demand

invocation_protocol:
  primary_pattern: hook_trigger
  hook_script: core/fss_hook.py
  hook_output_prefix: "[MICA]"
  hook_output:
    max_di_lines: 3
    di_filter: violations_only

update_triggers:
  - on_dogfood_cycle_close
  - on_explicit_save
  - on_hook_trigger

archive_policy:
  rotation: on_version_bump
  retention: indefinite
```

`di_filter: violations_only` ensures only DIs with recorded violations appear in hook output.
`max_di_lines: 3` caps output even if violation count grows.

---

## Example D — memory_injection + explicit (no hook)

```yaml
mica_spec: "0.2.4"
name: standalone-maintenance-agent
mode: memory_injection
description: "Project memory package invoked by operator command"

layers:
  - name: archive
    path: memory/standalone-maintenance-agent.mica.v1.0.0.json
    format: json
    loading_hint: always

  - name: playbook
    path: memory/standalone-maintenance-agent-playbook.v1.0.0.md
    format: markdown
    loading_hint: always

invocation_protocol:
  primary_pattern: explicit

update_triggers:
  - on_maintenance_complete

archive_policy:
  rotation: on_version_bump
  retention: indefinite
```

Use when the environment has no reliable hook surface.

---

## Archive DI Binding Examples (v0.2.4)

### Minimal binding (origin_episode only)

```json
{
  "id": "DI-001",
  "label": "no-whitespace-collapse-on-code",
  "statement": "Never apply re.sub(r'\\s+', ' ') to content containing code.",
  "severity": "critical",
  "binding": {
    "origin_episode": "EXP-017: re.sub collapse broke Python indentation, CI failed on 3 modules"
  }
}
```

### Full binding (all fields)

```json
{
  "id": "DI-002",
  "label": "billing-thresholds-are-measured",
  "statement": "STABLE_THRESHOLD=3 and CHUNK_CHARS=512 are verified constants. Changes require re-running the 10-session savings simulation.",
  "severity": "critical",
  "binding": {
    "origin_episode": "EXP-023: lowering STABLE_THRESHOLD to 1 caused unstable chunks to cache, savings dropped 40%",
    "violation_count": 1,
    "lesson_ref": "memory/lessons/2026-04-threshold-incident.md",
    "last_triggered": "2026-04-15"
  }
}
```

### Unbound DI (v0.2.3-style, still valid — PCT-010 WARN)

```json
{
  "id": "DI-003",
  "label": "hook-is-the-only-claude-readable-path",
  "statement": "Hook stdout is the only path that reaches Claude context.",
  "severity": "critical",
  "rationale": "Discovered 2026-04-07 audit. bat file echo does not reach context."
}
```

PCT-010 warns for unbound critical DIs. CLOSED CONTRACT status is preserved.
Add `binding` progressively — not speculatively.

---

## Notes

- `loading_hint: hook` is only valid when `primary_pattern: hook_trigger` is declared.
- `di_filter: violations_only` requires `violation_count` to be set in `binding`; otherwise
  the DI is treated as zero-violation and suppressed.
- `binding.lesson_ref` paths are validated by PCT-011 for file existence.
  A broken `lesson_ref` is worse than no `lesson_ref` — it asserts evidence that cannot be read.
- Use `tools/mica_runtime.py --format hook` to generate canonical hook output.
