# MICA Schemas

This directory contains machine-readable contracts used by the MICA tools and
their validators. It is not part of the session entrypoint.

Consumers start with `README.md`, then the declared `mica.yaml`, then the
selected archive and playbook. Do not copy these schemas into a consumer
repository unless that repository explicitly needs to validate a MICA artifact.

The active contracts are limited to:

- `mica.yaml.schema.json` for the repository manifest
- `mica.invocation.schema.json` for digest-bound invocation traces
- `mica.handoff.schema.json` for optional cross-session handoffs

Flow and memory-record schemas are not shipped. Their prior files were never
applied by a runtime validator, so publishing them overstated the product
contract.

Schema filenames and `$id` values are stable. Tool code resolves them through
`mica_primitives.find_shipped_schema()` rather than depending on repository-root
layout.
