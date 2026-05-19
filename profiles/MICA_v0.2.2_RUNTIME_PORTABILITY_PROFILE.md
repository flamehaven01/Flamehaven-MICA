# MICA v0.2.2 — Runtime Portability Profile

## Goal

MICA should remain usable across multiple AI runtimes without rewriting the archive contract.

The portability strategy is:

- keep the memory standard in package files
- move runtime logic into Python core tooling
- let each environment bind to that core through a thin adapter

---

## Core vs Adapter

### Core (portable)

Portable core assets:

- `mica.yaml`
- archive JSON
- playbook markdown
- `tools/mica_pct.py`
- `tools/mica_runtime.py`

These should work in any environment that can run Python.

### Adapters (environment-specific)

Examples:

- Claude Code `UserPromptSubmit`
- editor startup task
- shell alias / wrapper
- agent framework pre-run hook
- CI sanity check

Adapters must stay thin. They should not duplicate archive interpretation logic.

---

## Adapter Responsibilities

An adapter may do one or more of the following:

1. detect project root
2. call `mica_pct.py`
3. call `mica_runtime.py`
4. inject or display runtime summary
5. short-circuit if MICA is inactive

An adapter should NOT:

- redefine archive semantics
- reinterpret DI severity differently from core
- carry its own parallel copy of package state rules
- implement `hook_output` filtering independently — delegate to `mica_runtime.py`

---

## Recommended Binding Patterns

### Pattern A — CLI explicit invocation

```bash
python tools/mica_pct.py .
python tools/mica_runtime.py . --format text
```

Best for broad compatibility.

### Pattern B — Hook adapter

```bash
python tools/mica_runtime.py . --format hook
```

Best for per-prompt invariant activation.
`hook_output` policy in `mica.yaml` is automatically applied by `mica_runtime.py`.

### Pattern C — JSON bridge

```bash
python tools/mica_runtime.py . --format json
```

Best for editor extensions, MCP wrappers, or orchestration layers that want to render their own UI.

---

## Portability Rule

If a new environment can run Python but cannot support hook stdout injection, MICA should still operate through explicit CLI or JSON bridge mode.

That is the difference between:

- `MICA as a standard`
- and `hook_trigger as one strong adapter`

---

## Design Implication for Future Versions

The standard becomes more universal by strengthening the Python core and keeping adapters thin, not by adding more execution text to README.

v0.2.4 reinforces this: `hook_output` policy lives in `mica.yaml` and is executed by
`mica_runtime.py`. Adapters need no change to support the new volume control.
