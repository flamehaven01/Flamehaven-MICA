# MICA v3.1.0

Release date: 2026-09-04

## What Changed

MICA's public path is again the path its name describes:

```text
README.md -> mica.yaml -> archive + playbook -> session context
```

`primary_pattern: readme_protocol` is no longer an enum label only. The package
must contain one `MICA:INVOKE` directive near the top of `README.md`, and the
directive must resolve to the same `mica.yaml` the tools use.

`mica_runtime.py --format context` emits the exact selected agent-context bytes.
It includes profile-selected markdown sections, excludes operator-only surfaces,
checks the bytes against resolution evidence, and refuses an incomplete
contract.

Flow checks now run only when a package declares `flow_policy`. Existing flow
packages retain their checks; ordinary archive-and-playbook packages no longer
print five inactive flow results.

## Migration

A package that explicitly declares `readme_protocol` must place this near the
top of its README:

```markdown
<!-- MICA:INVOKE manifest="mica.yaml" -->
```

Use `manifest="memory/mica.yaml"` when that is the actual package manifest.
There must be exactly one directive and the path must be repository-relative,
canonical, and use forward slashes.

Then use:

```bash
python tools/mica_runtime.py . --format context
```

Five of six locally known consumers explicitly declared `readme_protocol`
without the directive and therefore become INCOMPLETE under v3.1.0. The sixth
does not declare that protocol and retains compatibility behavior. This release
does not modify consumer repositories automatically.

## What Was Removed

The unexecuted profile-outcome pilot, duplicate or memory-engine-oriented
starter templates, and superseded evolution, execution, recovery, and
context-continuity plans were removed from the current tree. Git history retains
them.

Flow, handoff, invocation evidence, measurement, and structured-memory tools
remain available as optional support. They are not the default product path.

## Other Included Fixes

Since v3.0.2, `mica_measure.py` now carries every PCT-006 compatibility warning
without filtering or dropping a second warning. CI also runs on every branch so
a candidate commit can satisfy required checks before a protected-main
fast-forward. These are support fixes, not a new MICA product direction.

## Version Boundary

This is tool release `3.1.0`. The package contract version remains `0.2.9`, and
the enumerated supported contract set remains `0.2.4` through `0.2.9`. Tool and
contract versions are independent.

## Verification

- Python 3.9, 3.11, 3.12, and 3.13 remain the CI matrix.
- Local pre-release verification: 386 passed, 1 skipped.
- README examples, schema metavalidation, fixture snapshots, lint, and format
  checks are included in the suite.

The tests establish local contract resolution and context emission. They do not
prove that an external model host attached, understood, or obeyed the emitted
context.
