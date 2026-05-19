# MICA v0.2.4 — Hook Output Profile

## Purpose

`hook_output` policy controls what appears in hook-format MICA output.
This profile defines when to apply it, how to configure it, and the trade-offs
between signal density and context noise.

---

## When to Use

Apply `hook_output` when:

- `primary_pattern: hook_trigger` is declared
- the project has 3 or more critical DIs
- most DIs have no recorded violations and add low signal to each prompt
- hook context length is a concern

Omit `hook_output` when:

- all critical DIs have recorded violations (nothing to suppress)
- hook context length is not a concern
- v0.2.3 behavior is acceptable and preferred

Omitting `hook_output` preserves v0.2.3 behavior exactly.

---

## Configuration

```yaml
invocation_protocol:
  primary_pattern: hook_trigger
  hook_script: core/my_hook.py
  hook_output_prefix: "[MICA]"
  hook_output:
    max_di_lines: 3
    di_filter: violations_only
```

### max_di_lines

| Value | Behavior |
|-------|----------|
| absent / 0 | Unlimited — all DIs matching filter appear |
| 1 | At most 1 `[MICA:DI]` line |
| N | At most N `[MICA:DI]` lines (cap applied after filter) |

Cap is applied after `di_filter`. If `di_filter: violations_only` produces 2 DIs
and `max_di_lines: 5`, both appear (cap is not reached).

### di_filter

| Value | Behavior |
|-------|----------|
| `all` (default) | All critical DIs appear in hook output |
| `violations_only` | Only DIs with `binding.violation_count > 0` appear |

`violations_only` requires `binding.violation_count` to be set on the DI.
DIs without `binding`, or with `violation_count` absent or `0`, are treated as
zero-violation and suppressed.

---

## Output Format

### Without hook_output (or `di_filter: all`)

```text
[MICA] project-name v1.0.0 | mode=protocol_evolution | pattern=hook_trigger | DI=3crit/2high | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): no-whitespace-collapse-on-code [2x]
[MICA:DI] DI-002(critical): no-fss-optimized-marker
[MICA:DI] DI-003(critical): chunk-cache-thresholds-are-tested [1x]
```

### With `di_filter: violations_only`

DI-002 has no `violation_count`, so it is suppressed:

```text
[MICA] project-name v1.0.0 | mode=protocol_evolution | pattern=hook_trigger | DI=3crit/2high | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): no-whitespace-collapse-on-code [2x]
[MICA:DI] DI-003(critical): chunk-cache-thresholds-are-tested [1x]
```

### With `max_di_lines: 1, di_filter: violations_only`

```text
[MICA] project-name v1.0.0 | mode=protocol_evolution | pattern=hook_trigger | DI=3crit/2high | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): no-whitespace-collapse-on-code [2x]
```

The `[Nx]` suffix appears only when `binding.violation_count > 0`.

---

## Signal Trade-offs

| Configuration | Signal | Noise | Best for |
|--------------|--------|-------|---------|
| No `hook_output` | High — all DIs visible | High — unviolated DIs pollute context | Small projects with few critical DIs |
| `di_filter: violations_only` | Higher per-line — only proven risks | Low | Projects with mixed violation history |
| `max_di_lines: N` | Capped but predictable | Minimal | High-DI projects, strict token budget |
| Both combined | Densest signal | Lowest noise | Production hook-trigger deployments |

---

## Design Constraint

`hook_output` policy is interpreted by `mica_runtime.py --format hook`.
If the hook adapter bypasses `mica_runtime.py` and emits DI lines directly,
the policy has no effect.

The preferred hook adapter:

```python
import subprocess
result = subprocess.run(
    ["python", "tools/mica_runtime.py", ".", "--format", "hook"],
    capture_output=True, text=True
)
print(result.stdout, end="")
```

Adapters must not duplicate archive parsing. Call `mica_runtime.py` — forward stdout.

---

## Relationship to DI Binding

`di_filter: violations_only` depends on `binding.violation_count` being set.

If a project uses `di_filter: violations_only` but has no DIs with `violation_count`,
all DIs are suppressed and hook output contains only the summary line.
This is a valid low-noise state, but it means the hook carries no DI signal.

Preferred setup: add `binding.violation_count` to DIs as violations are recorded,
then enable `di_filter: violations_only`. The filter becomes meaningful as the
archive accumulates evidence.

See `profiles/MICA_v0.2.4_DI_BINDING_PROFILE.md` for `violation_count` authoring rules.
