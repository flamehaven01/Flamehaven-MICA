# MICA v3.3.1

Release date: 2026-09-05

## Applied Contract Surface

MICA remains a repository-owned invocation contract:

```text
README -> mica.yaml -> archive + playbook -> emitted session context
```

This patch removes published schemas that no MICA runtime validator applied.
The retained machine-readable contracts are limited to:

- `mica.yaml.schema.json` for repository manifests
- `mica.invocation.schema.json` for digest-bound invocation traces
- `mica.handoff.schema.json` for optional cross-session handoffs

Flow and memory-record schema files were specification artifacts without a
validator-backed runtime path. They no longer ship as product contracts.
Optional flow behavior remains unchanged; this release does not infer that
existing flow records are invalid.

## External Field Validation

MICA now provides a structured [field-validation issue form](../.github/ISSUE_TEMPLATE/field-validation.yml)
for independent adoption and operation attempts. The associated product-boundary
guidance preserves the first attempt, reproduces before editing, and routes
host-specific or repository-specific friction outside MICA core.

## Distribution Layout

Machine-readable schemas now live in [`schemas/`](../schemas/README.md), not
the repository root. Runtime schema resolution is centralized in the tools.
Consumers that directly hard-coded a schema filesystem path must update it to
`schemas/`; retained schema filenames and `$id` values are stable.

## Verification

- Local suite: 391 passed, 1 symbolic-link case skipped on Windows.
- Ruff lint and formatting: passed.
- The three retained schemas passed JSON Schema meta-validation.
- Minimal-package context emission and optional handoff validation passed.

These checks establish the local release candidate. Remote CI and immutable tag
publication remain required before calling this version released.
