# MICA v3.0.0 Declaration

## Status

Working declaration for the intended major reset after the current `v0.2.9` draft cycle.

This is not a release note.
It is the statement of intent that defines what `v3.0.0` is supposed to mean.

## Central judgment

`v3.0.0` should make MICA unambiguously invocation-first again.

MICA is not primarily a governance scorekeeper.
MICA is not primarily a general memory store.
MICA is a portable invocation contract for AI memory surfaces.

Its primary responsibilities are:

1. locate the correct memory package at session start
2. load the correct context surfaces
3. activate the session against the correct invariants
4. declare truthfully what was and was not loaded
5. preserve an auditable record of that invoked state

## Why this reset is necessary

The `v0.2.9` drafts improved MICA in useful ways:

- observation capture
- promotion provenance
- recall telemetry
- slots and graph projections
- memory-first export structure

But those drafts also shifted the center of gravity toward governed memory substrate design.
That work is valuable, but it is not the original center of MICA.

Without an invocation-first reset, the project risks becoming:

- a governance layer over stored memory
- a memory substrate with export controls
- a collection of useful archival tools

All of those are adjacent to MICA.
None of them, by themselves, fully satisfy the name `Memory Invocation & Context Archive`.

## What v3.0.0 means

`v3.0.0` should mean that MICA once again treats invocation as the top-level contract.

That requires four things to become first-class:

### 1. Invocation contract

The package must define, normatively:

- which surfaces are always loaded
- which surfaces are conditionally loaded
- which surfaces are operator-only
- which surfaces may enter `agent_context`
- what counts as successful invocation

### 2. Context-loading contract

Runtime must describe not only what exists in the package, but what was actually loaded for the current session.

That includes at least:

- archive
- playbook
- slot surfaces
- approved recall surfaces
- active governed invariants

### 3. Truthful loaded-state output

Session summary should answer a stricter question than package validation.

It should answer:

> what context did this session actually invoke?

That output should make omissions and degradations explicit rather than implied.

### 4. Auditable invocation trace

MICA should preserve a durable record of:

- invoked surfaces
- injected context surfaces
- active governed facts during the session
- degraded or unavailable optional surfaces

## What remains subordinate

Governance is still important.
Memory-first substrate work is still important.
They remain inside the system, but no longer as the headline identity.

They should be treated as subordinate layers that support the invocation contract:

- governance protects truth depth
- promotion protects archive quality
- memory-first layers improve persistence and operational usefulness
- recall and slots improve context ergonomics

None of them should redefine the project away from invocation.

## Relationship to v0.2.9

The current `v0.2.9` branch should be interpreted as groundwork, not destination.

It contributes:

- schemas
- fixtures
- runtime split between core and flow
- observation and promotion discipline
- memory-first operational artifacts

`v3.0.0` should inherit that work where it helps, but it should not inherit the framing error that places governance or storage above invocation.

## Release boundary for v3.0.0

`v3.0.0` should not be declared complete unless all of the following are true:

1. invocation rules are normative for archive-first and memory-first packages
2. context-loading rules for `agent_context` are explicit and enforceable
3. runtime output reports actual invoked surfaces truthfully
4. invocation traces are auditable artifacts, not implied behavior
5. governance and memory-first layers are documented as supporting layers, not the core identity

## Short declaration

> MICA v3.0.0 is the release that restores MICA's original meaning: truthful invocation of the right memory context at the session boundary, with governance and memory storage remaining subordinate supporting layers.