# MICA v0.2.2 — Hook Trigger Profile
## (Updated for v0.2.4: hook_output policy)

## Purpose

`hook_trigger` is the strongest MICA invocation pattern when the runtime can inject hook stdout into model context before every prompt.

This profile defines:

- when hook-trigger should be used
- what the hook must emit
- how the AI must interpret that output
- where the hook pattern stops being portable

---

## When to Use

Use `hook_trigger` when:

- a pre-prompt hook already exists
- the hook is maintained as part of the project
- the runtime can inject hook stdout into model context
- the hook remains fast enough for normal interaction

Do not use `hook_trigger` when:

- the runtime has no pre-prompt hook surface
- the hook would need expensive subprocess work for every prompt
- the environment cannot guarantee hook output reaches the model

---

## Required mica.yaml shape

```yaml
invocation_protocol:
  primary_pattern: hook_trigger
  hook_script: core/my_hook.py
  hook_output_prefix: "[MICA]"
```

With v0.2.4 volume control (optional):

```yaml
invocation_protocol:
  primary_pattern: hook_trigger
  hook_script: core/my_hook.py
  hook_output_prefix: "[MICA]"
  hook_output:
    max_di_lines: 3
    di_filter: violations_only
```

Recommended archive layer setting:

```yaml
- name: archive
  path: memory/my-project.mica.v1.0.0.json
  format: json
  loading_hint: hook
```

---

## Preferred Hook Implementation

The preferred hook implementation is:

```bash
python tools/mica_runtime.py [project_root] --format hook
```

This keeps runtime summary generation in the portable Python layer instead of duplicating archive parsing logic inside each hook script.

The hook adapter should only:

1. call `mica_runtime.py`
2. forward stdout
3. exit `0` even if MICA load fails

---

## Required Output

First line:

```text
[MICA] my-project v1.0.0 | mode=memory_injection | pattern=hook_trigger | DI=2crit/1high | pct=CLOSED | last=2026-04-08
```

Then one line per critical invariant (subject to hook_output policy in v0.2.4):

```text
[MICA:DI] DI-001(critical): no-destructive-reset [2x]
```

The `[Nx]` suffix appears only when `binding.violation_count > 0`.

Keep the output terse. High and lower invariants should not appear in hook output
unless the project has an explicit reason.

When `hook_output: {di_filter: violations_only}` is set, DIs without recorded violations
are suppressed. See `profiles/MICA_v0.2.4_HOOK_OUTPUT_PROFILE.md`.

---

## AI Behavior

On receiving hook lines:

1. acknowledge in one terse line only
2. do not print a second verbose session opening report
3. treat critical DI lines as active session guards with binding evidence when present
4. if `pct != CLOSED`, run `mica_pct.py` before structural changes

Recommended acknowledgment:

```text
[MICA] loaded via hook. 2 critical DIs active. (pct=CLOSED)
```

When a guard fires, surface binding evidence if present:

```text
[GUARD] DI-001 no-destructive-reset: about to run git reset --hard
Evidence: EXP-017: force-reset deleted uncommitted work [2x violated]
Proceed? This requires explicit acknowledgment.
```

---

## Design Constraint

Hook-trigger improves invocation reliability, but it is not the whole standard.

The portable contract is:

- `mica.yaml`
- archive
- playbook
- `mica_pct.py`
- `mica_runtime.py`

The hook is an adapter on top of that core.
`hook_output` policy is interpreted by `mica_runtime.py`, not by the hook adapter itself.
