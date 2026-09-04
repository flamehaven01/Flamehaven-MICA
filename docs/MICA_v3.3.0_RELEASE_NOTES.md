# MICA v3.3.0

Release date: 2026-09-04

## Repository-Owned Memory Lifecycle

MICA remains an invocation and context-loading contract:

```text
README -> manifest -> archive + playbook -> session context
```

v3.3.0 makes that path easier for another AI to use and maintain without
turning MICA into an automatic memory generator or imposing one archive shape
on independently evolved repositories.

## AI Use and Authoring Skills

[`mica-context`](../skills/mica-context/SKILL.md) remains the consumption path.
It enters through the target README, resolves the declared manifest and
profile, emits the selected archive and playbook, and reports what was actually
loaded.

[`mica-author`](../skills/mica-author/SKILL.md) is a separate, explicitly
requested authoring path. It requires current repository evidence, invokes an
existing package before editing it, preserves repository-owned paths and
vocabulary, and ends by running the PCT and context emitter. It does not infer
durable decisions or invariants from source-code summaries.

The authoring guide now covers creation, maintenance, context optimization, and
retirement. A smaller context is treated as cheaper, not automatically better;
work-quality claims still require outcome evidence.

## Consumer Integration

Thin one-line `CLAUDE.md` and `AGENTS.md` adapters point agent hosts to the
canonical skill and runtime without copying MICA policy into each consumer.

Three executable archetypes exercise repository shapes already seen in use:

- a legacy root manifest with versioned archive and playbook names
- profile-selected physical playbooks
- a nested `memory/mica.yaml` reached through an existing launcher

Each archetype validates and emits real archive and playbook bytes. Existing
consumers do not need to rename files, change archive schemas, or migrate to the
minimal package.

The reusable workflow remains optional and is pinned as:

```yaml
jobs:
  mica:
    uses: flamehaven01/Flamehaven-MICA/.github/workflows/mica-consumer.yml@v3.3.0
    with:
      project-root: .
      profile: default
```

## Deliberate Boundaries

- No runtime, invocation-contract schema, or PCT behavior changed.
- No automatic memory-authoring command was added.
- No existing consumer package was rewritten or normalized.
- No complexity refactor was performed solely to improve a static score.
- A closed contract still proves resolution and emission, not model cognition
  or improved task outcomes.

The read-only
[static analysis snapshot](MICA_SLOP_SCAN_2026-09-04.md) records structural
hotspots at revision `a7ac0b3`. It is evidence for future diagnosis, not a CI
gate or an instruction to refactor.

## Verification

- Test collection: 397 tests.
- Local Windows suite: 396 passed, 1 symbolic-link case skipped.
- Remote Linux CI: all 397 tests passed on Python 3.9, 3.11, 3.12, and 3.13;
  the memory-contract job also passed.
- Both `mica-context` and `mica-author` passed the skill validator.
- README examples, golden PCT output, all fixtures, and all three consumer
  archetypes passed.

These checks establish the released distribution and its invocation surfaces.
They do not establish that an external model understood or obeyed emitted
context.

## Version Axes

- Tool release: `3.3.0`
- MICA contract version: `0.2.9`
- Supported contract versions: explicitly enumerated by the released tools
- Consumer project and artifact versions: owned by each repository
