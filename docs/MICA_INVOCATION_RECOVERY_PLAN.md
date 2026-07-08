# MICA Invocation Recovery Plan

## Status

Working note after the first v0.2.9 draft cycle.

This document does not reject the current governance and memory-first work.
It re-centers the project on the part of MICA that was original, distinctive, and still necessary:
portable memory invocation with truthful context declaration.

## Original objective recovered from repo history

Across the early specs, the core meaning of MICA was consistent:

- v0.2.4 defined `mica.yaml` as the composition contract for a memory package
- v0.2.5 defined runtime entry states, detection order, and required session summary behavior
- v0.2.7 explicitly defined the core boundary as:
  - memory invocation
  - AI session activation
  - truthful loaded-state declaration before work begins

The original center of gravity was therefore not "store more memory."
It was:

1. identify the correct memory package
2. load the correct context surfaces
3. activate the session against the right invariants
4. say truthfully what was and was not loaded

That is what makes the name `Memory Invocation & Context Archive` coherent.

## What changed

The later v0.2.9 drafts added two strong but different expansion paths:

- governed observation-to-promotion flow
- memory-first substrate with sessions, memories, recall, slots, and graph

Both are useful.
Both improve the system.
Neither is the same as closing the invocation contract.

As a result, the project became stronger at:

- provenance
- promotion discipline
- memory export
- archive truth

But comparatively weaker, in emphasis, at:

- session-start invocation
- context loading policy
- agent-context truth declaration
- trace of what was actually invoked

## Current diagnosis

At the current draft stage, MICA is best described as:

- governance-centered memory substrate
- archive/export truth system

It is not yet fully satisfying its own name as:

- memory invocation system
- context archive whose runtime loaded state is first-class and auditable

This is not a failure.
It is a prioritization drift.

## The recovery principle

Memory-first work should remain below the contract, not replace the contract.

That means:

- `observations`, `memories`, `recall`, `slots`, and `graph` are operational substrate layers
- `archive`, `playbook`, and invocation summary remain the contract-facing surfaces
- runtime truth must describe what the agent actually received, not only what the package can export

## What must be restored to the primary track

### 1. Invocation contract

MICA needs a normative answer to:

- which layers are always loaded
- which layers are conditionally loaded
- which layers are never silently inferred
- what counts as successful invocation

This should be explicit for:

- archive-first packages
- compact/legacy packages
- memory-first packages

### 2. Context loading contract

MICA needs a normative answer to:

- what may enter `agent_context`
- what remains operator-only
- whether `slots` are mandatory context surfaces
- whether `recall` is context, telemetry, or both

Without this, memory-first artifacts exist, but "context archive" remains only partially realized.

### 3. Loaded-state truth output

Runtime output should move from generic package summary toward invoked-state summary.

The primary question should become:

"What did the current session actually load and rely on?"

That includes:

- invoked package mode
- loaded surfaces
- omitted surfaces
- promoted truths active in context
- degraded or unavailable optional flow surfaces

### 4. Invocation trace

Archive truth should eventually preserve not only exported memory, but also invocation truth.

At minimum, MICA should be able to answer:

- which context surfaces were invoked
- which slot or recall surfaces entered the session
- which governed facts were active during the session

## Recommended next version boundary

The next serious step should not be "more memory features first."
It should be "invocation closure first."

Recommended priority:

1. freeze invocation contract for archive-first and memory-first modes
2. freeze context loading rules for `archive`, `playbook`, `slots`, and approved recall
3. extend runtime output to report actual invoked surfaces
4. add invocation trace as an auditable artifact
5. only then expand retrieval breadth, graph querying, or richer memory ergonomics

## Concrete v3.0.0 direction

If a v3.0.0 line is declared, its central judgment should be:

> v3.0.0 is the release that makes MICA a truthful invocation contract for governed memory surfaces, not only a governance layer over stored memory.

That would let v0.2.9 remain valuable for governance and memory-first groundwork,
while giving the project a clear path back to the meaning of its own name.

## Short verdict

The current branch has improved MICA's depth.
The next branch should recover MICA's center.

That center is not memory accumulation by itself.
It is truthful invocation of the right memory context at the right session boundary.