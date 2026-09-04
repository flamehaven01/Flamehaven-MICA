# MICA Consumer Authoring Guide

## Purpose

This guide is for maintainers adding MICA to another repository and for AI agents that
will operate that package. MICA is an invocation and context-loading contract: it tells
the session which memory surfaces to load, which invariants apply, and what was actually
invoked. It is not a request to turn the target repository into a generic memory engine.

## Start With the Complete Package

Use [the minimal package](../templates/minimal-package/) for a normal,
single-domain repository. It establishes the whole invocation chain:

```text
repo/
  README.md
  mica.yaml
  memory/
    mica_archive.json
    mica_playbook.md
```

Use a router playbook with on-demand domain playbooks only when the repository has
separate operational lanes. Keep every `always` surface short enough to be read at
session start. A package is invalid if the agent must guess which file contains the
current archive or procedure.

## Write the Four Assets

### `README.md`

Put exactly one `<!-- MICA:INVOKE manifest="mica.yaml" -->` directive near the
top and tell the session to run `python tools/mica_runtime.py . --format
context`. Keep archive and playbook paths out of README prose; `mica.yaml` owns
them.

### `mica.yaml`

Declare the package composition, paths, and loading hints. `archive` and `playbook`
must be `always`. When `agent_context_surfaces` is declared, declare
`primary_pattern` explicitly as well; do not rely on the runtime default. Add
`agent_context_surfaces` only for surfaces that are safe and necessary at session start.
Keep human-review evidence out of agent context through `operator_only_surfaces` when
the target package uses that distinction.

### Archive

Store durable project identity, design invariants, binding provenance, and decisions
that future work must honor. Do not use it as a work log, scratchpad, or unreviewed
recall store.

### Playbook

Write an executable operating guide for both people and AI agents. Begin with a session
start sequence that says exactly which declared surfaces to load, which project rules
apply, what must be checked before editing, and how to report an incomplete invocation.
Put detailed domain procedure and verification commands here, not in `mica.yaml`.

Use [MICA_AGENT_GUIDE.md](../templates/MICA_AGENT_GUIDE.md) as the starting wording.
Replace every placeholder and remove instructions that do not apply to the target.

## AI Maintainer Contract

An AI operating a MICA-enabled repository must:

1. Read the README invocation directive rather than guessing the manifest path.
2. Run the context emitter and stop if the contract is incomplete.
3. Resolve the active memory profile first: a requested one, or `default` if
   the package declares profiles. What it names is what this session loads.
   Fall back to `always` layers plus task-relevant on-demand layers only when
   the package declares no profiles at all.
4. Follow the emitted archive invariants and playbook procedures before local preference.
5. Stop and report a missing, conflicting, or unverifiable required surface.
6. Keep operator-review material separate from agent context unless explicitly declared otherwise.
7. Report verification actually run, rather than claiming a generic ready state.

## Runtime-Backed Consumers

A target may use archive values in product code, for example to read a pre-registered
gate threshold. In that case, resolve the archive layer from `mica.yaml` at runtime;
do not hard-code a versioned archive filename. Fail loudly when the declared archive is
missing, ambiguous, malformed, or escapes the repository root.

This does not make MICA a product runtime dependency. The target owns its small local
composition resolver and its behavior tests. MICA tools remain operator-side validation
and invocation utilities.

## Invocation Evidence

`MICA CONTRACT RESOLVED` means declared surfaces were found and resolved. It does not
prove an AI read them. To record a timestamped resolved invocation, run:

```powershell
python <MICA_ROOT>/tools/mica_runtime.py . --write-invocation-trace
python <MICA_ROOT>/tools/mica_invocation.py memory/mica.invocation.jsonl
```

A valid trace is `recorded` provenance. In a package without a session or observation
stream, `session_id` may be `null`; do not present that trace as uniquely identified
AI-session evidence. Report `declared`, `resolved`, and `recorded` states separately.

## Do Not Duplicate MICA

The canonical package contract and generic authoring guidance remain in MICA. A target
repository should contain only its own paths, invariants, procedures, and validation
commands. Link to MICA for generic explanation instead of copying a second evolving
standard into every consumer repository.

## Acceptance Check

- README contains one valid `MICA:INVOKE` directive near the top.
- The directive resolves to the package's `mica.yaml`.
- Every `always` layer exists and can be loaded without filename inference.
- The playbook contains a concrete session-start sequence and a project verification route.
- `mica_runtime.py --format context` emits archive and playbook bytes.
- The package distinguishes resolved, emitted, and recorded states.
- A target that consumes archive values in code resolves the archive through `mica.yaml`.
