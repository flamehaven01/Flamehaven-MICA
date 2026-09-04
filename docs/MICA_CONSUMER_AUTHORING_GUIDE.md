# MICA Consumer Authoring Guide

## Purpose

This guide is for maintainers adding MICA to another repository and for AI agents that
will operate that package. MICA is an invocation and context-loading contract: it tells
the session which memory surfaces to load, which invariants apply, and what was actually
invoked. It is not a request to turn the target repository into a generic memory engine.

## Start With the Repository

First inspect the repository's existing README, durable project memory, and
operating instructions. MICA standardizes how those materials enter a session;
it does not require repositories that evolved independently to use identical
filenames or archive schemas.

For a new package, [the minimal package](../templates/minimal-package/) is a
scaffold for the invocation chain:

```text
repo/
  README.md
  mica.yaml
  memory/
    mica_archive.json
    mica_playbook.md
```

Existing packages may place the manifest under `memory/`, use versioned archive
names, or route between domain playbooks. Preserve that repository-specific
shape when its README and manifest resolve it unambiguously. Keep every selected
session-start surface short enough to be read. A package is invalid if the agent
must guess which file contains the current archive or procedure.

## Define the Four Roles

### `README.md`

Put exactly one `MICA:INVOKE` directive near the top. Its `manifest` value may
name `mica.yaml`, `memory/mica.yaml`, or another repository-relative path. Tell
the session how to run the matching context emitter. Keep archive and playbook
paths out of README prose; the selected manifest owns them.

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

Use [MICA_AGENT_GUIDE.md](../templates/MICA_AGENT_GUIDE.md) as optional starting
wording. Replace every placeholder and remove instructions that do not apply to
the target. Agent hosts that support skills can use
[`skills/mica-context/SKILL.md`](../skills/mica-context/SKILL.md) instead of
copying generic instructions into every repository.

Use [`skills/mica-author/SKILL.md`](../skills/mica-author/SKILL.md) only when a
user explicitly asks to create or change a MICA package. The context skill
consumes repository memory; the author skill changes what later sessions will
receive.

When a host requires `CLAUDE.md` or `AGENTS.md`, use the corresponding
[one-line adapter](../templates/adapters/). Keep it as a pointer to the
`mica-context` skill and runtime fallback. Repository-specific policy belongs
in the emitted playbook, not in a second host-specific copy.

## AI Maintainer Contract

An AI operating a MICA-enabled repository must:

1. Read the README invocation directive rather than guessing the manifest path.
2. Run the released, vendored, or repository-provided context emitter and stop
   if the contract is incomplete.
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

## Consistent Use, Adaptive Shape

The stable cross-repository behavior is:

1. README identifies the manifest.
2. The manifest selects repository-owned memory surfaces.
3. The runtime emits the selected archive and playbook.
4. The AI applies relevant retained memory and operating procedure to its task.
5. The session reports what was actually loaded and verified.

The stable behavior is not a demand for one directory tree, archive schema,
playbook vocabulary, or amount of memory. Those remain local design choices.

## Artifact Lifecycle

An existing MICA package is an independent, repository-owned object. Invoke it
before editing it, preserve its established paths and vocabulary, and do not
retrofit it to the current starter layout merely for consistency.

For a new package, create the four roles from current repository evidence and
then prove that the declared archive and playbook emit as context. Maintain the
archive when a durable decision, invariant, or incident changes retained project
truth. Maintain the playbook when the actual operating or verification method
changes. A transient session summary is not sufficient evidence for either.

When retiring memory, retain the repository's supersession or replacement
record. Remove a declared surface only after profiles, launchers, and runtime
consumers no longer reference it. MICA does not require one universal tombstone
format; the target repository owns that representation.

## Optimize Useful Context

Choose representative tasks and profiles before changing package composition.
Record which roles and bytes each profile emits, remove stale paths and
duplication, and place domain-only procedure behind the profile that needs it.
Required invariants must remain available wherever they apply.

Compare emitted roles and byte counts before and after the change, then run the
target repository's task-specific validation. A smaller context is cheaper, not
necessarily better. Do not claim improved work quality without outcome evidence.

## Keep Version Axes Separate

- The MICA tool release versions the validator and runtime distribution.
- `mica_spec` versions the invocation contract understood by those tools.
- The consumer repository owns its project or artifact version.

Do not label a consumer archive or playbook with the MICA tool release merely
because that tool created or validated it. This avoids turning independently
evolved repository memory into centrally versioned MICA output.

## Acceptance Check

- README contains one valid `MICA:INVOKE` directive near the top.
- The directive resolves to the package's selected manifest.
- Every `always` layer exists and can be loaded without filename inference.
- The playbook contains a concrete session-start sequence and a project verification route.
- `mica_runtime.py --format context` emits archive and playbook bytes.
- The package distinguishes resolved, emitted, and recorded states.
- A target that consumes archive values in code resolves the archive through `mica.yaml`.
