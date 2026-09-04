# MICA v3.2.0

## Consistent Use, Adaptive Memory

MICA grew inside repositories that had different histories, operating domains,
archive shapes, and playbook structures. v3.2.0 does not erase that adaptation.
It standardizes the behavior of an AI using MICA, not the internal form of each
repository's memory.

The shared protocol is:

1. Enter through the target repository's README.
2. Resolve exactly the manifest named by its `MICA:INVOKE` directive.
3. Select the requested or default profile without adding unselected surfaces.
4. Emit the selected archive and playbook as session context.
5. Apply relevant retained memory and repository procedure to the current task.
6. Report the selected profile, emitted surfaces, applied memory, and actual
   verification.

The archive remains retained repository memory. The playbook remains the
repository's operating method. Validation, CI, traces, and governance checks
are support and must not become the product path.

## AI Skill

[`skills/mica-context/SKILL.md`](../skills/mica-context/SKILL.md) packages that
use protocol for agent hosts that support repository skills. It instructs the
AI to adapt to manifest-declared paths and profiles, stop on failed emission,
and report conflicts between current evidence and retained memory.

The skill does not create an autonomous MICA agent. It also refuses to import a
general SDLC: planning, PR review, deployment, monitoring, flow, recall,
handoff, and trace machinery remain outside the default path unless the target
repository or user explicitly requires them.

The design takes one narrow lesson from AI-native SDLC practice: repeated agent
procedure belongs in a reusable skill, while deterministic checks belong in
CI. It does not make MICA an SDLC framework.

Design references: Anthropic's
[AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook)
and the project retrospectives on
[responsibility](https://flamehaven.space/writing/everyone-was-talking-about-ai-agents-we-were-asking-who-was-responsible/),
[memory-gate experiments](https://flamehaven.space/writing/when-the-memory-gate-met-a-real-archive-what-90-experiments-taught-us-about-cheap-llm-slop/),
and the
[README entrypoint gap](https://flamehaven.space/writing/the-readme-was-a-protocol-the-entrypoint-was-still-optional/).

## Consumer CI

The reusable [consumer workflow](../.github/workflows/mica-consumer.yml) checks
out the released MICA runtime, validates a consumer package, and emits the
selected context into the runner's temporary directory. Only the byte count is
written to the job summary. Archive and playbook contents are not uploaded as
artifacts.

This establishes `PASS[CI:context-emission]`, not proof that a model received,
understood, or obeyed the context during another session.

## Exact Context Bytes

The v3.1.0 context path hashed raw surface bytes but emitted text produced by
`Path.read_text()`. On Windows, a CRLF surface could therefore resolve against
one digest and be emitted with different LF bytes. The CLI now assembles and
writes context as bytes, preserving full-surface line endings and checking the
emitted payload against resolution evidence.

## Removed Authoring Subsystem

`tools/mica_memory.py` and its isolated authoring tests are removed. No other
MICA tool imported the module, a read-only census of known consumers found no
callers, and public code search found no external use. Keeping more than one
thousand lines of unused session/memory/slot/graph synthesis code made MICA look
like a general memory engine rather than an invocation contract.

This is not removal of memory. Pre-materialized `memory_first` packages remain
readable, and the schemas and fixture needed to invoke their exported archive
and playbook remain available for compatibility.

## Migration

Existing MICA consumers do not need to rename memory files or adopt the minimal
template. Add or correct the README directive if the package declares
`readme_protocol`, then invoke the manifest and surfaces already owned by that
repository. The minimal package is a scaffold only for repositories that do
not yet have a usable memory organization.

Consumers may add the reusable workflow:

```yaml
jobs:
  mica:
    uses: flamehaven01/Flamehaven-MICA/.github/workflows/mica-consumer.yml@v3.2.0
    with:
      project-root: .
      profile: default
```

Repositories with a nested manifest, custom profile, or repository-specific
runtime command should pass their actual root/profile and preserve their
existing package shape.

## Deliberate Non-Goals

- No uniform archive schema or filename convention was imposed.
- No standalone MICA agent was introduced.
- No deployment, monitoring, PR-review, or general SDLC subsystem was added.
- `mica_core.py` was not split merely to improve line counts; that would move
  support code without reducing it.
- No claim is made that MICA improves task outcomes without a controlled study.

## Version Axes

- Tool release: `3.2.0`
- MICA contract version: `0.2.9`
- Supported contract versions: enumerated by the released tools
