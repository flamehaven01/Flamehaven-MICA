# MICA Product Boundary

Status: **FROZEN at v3.3.1 until external evidence justifies a change.**

## Definition

> MICA is a vendor-neutral contract that invokes repository-owned memory and
> playbooks as verifiable session context.

The product path is:

```text
README -> mica.yaml -> selected archive + playbook -> emitted session context
```

Profiles select repository-owned surfaces. PCT checks whether the invocation
contract resolves. Exact-byte evidence and invocation traces describe what was
resolved or emitted. They do not prove memory quality, author identity, model
comprehension, or improved task outcomes.

## Change Admission

MICA core work may reopen only for one of these observed inputs:

1. A real external consumer reproduces an invocation failure.
2. Repeated integration friction shows that the supported invocation path is
   impractical.
3. An independent consumer finds an ambiguity in the contract.
4. A reproducible defect, regression, or security issue affects selection,
   isolation, resolution, or exact-byte emission.

Before accepting a change, answer both questions:

```text
Does it improve or repair the invocation contract itself?
Is the failure reproducible on a real consumer path?
```

If either answer is no, route the work outside MICA core.

| Request | Destination |
|---|---|
| Wrong manifest, profile, audience, or emitted bytes | MICA core candidate |
| Host-specific wiring | Thin adapter or consumer repository |
| Repository-specific memory structure or policy | Consumer repository |
| Outcome comparison or causal benchmark | Separate research repository |
| Author identity, signing, or organizational approval | Consumer governance layer |
| Automatic summarization, synthesis, or retrieval | Reject as a MICA core feature |

## External Field Validation

An independent consumer's first attempt is evidence. Do not replace it with a
guided second attempt before recording what happened. Ask the consumer to keep
the target repository, MICA release, host, task, commands, outputs, and first
blocking ambiguity identifiable. Secrets and private repository content must be
removed before public submission.

For each report, record:

- whether the task was adoption or operation
- target revision, MICA release, host, model, operating system, and Python version
- public instructions discovered and the order in which they were used
- exact commands, exit codes, and the first unexpected result
- emitted context byte count and how the host was asked to attach that context
- files created or changed, any intervention received, and expected versus actual behavior

Respond in this order:

1. Preserve the original report and acknowledge its current evidence boundary.
2. Reproduce against the reported MICA release and consumer shape before editing.
3. Classify the result using the destination table above.
4. Make a MICA change only for a reproduced core-contract defect or ambiguity.
5. Verify the narrow failure path and report remaining uncertainty. Do not turn
   successful resolution or emission into a claim about comprehension or outcome.

One consumer's preference is not automatically a product requirement. One
reproducible correctness defect can be sufficient; adoption friction should be
repeated or independently corroborated before expanding the product surface.

## Explicit Non-Goals

- automatic memory extraction or generation
- vector databases, embeddings, or semantic retrieval engines
- a universal archive schema or lifecycle engine
- host-wide delivery receipts unsupported by the host
- signing, IAM, or supply-chain governance as a core subsystem
- PR, deployment, monitoring, or general SDLC orchestration
- complexity refactors without a reproduced product-path failure
- claims that emitted context improved model behavior without outcome evidence

Integrity-verifiable does not mean identity-authenticated. Archive structural
checks do not establish that retained memory is true or useful.

## Research Boundary

Research may consume MICA output, but it must not turn its harness into MICA
product code. A causal benchmark belongs in a separate repository and must bind
the treatment context to the actual experimental request before interpreting
outcomes. Sample size follows the study design and observed variance, not a
fixed product gate.

## Distribution Boundary

Packaging or additional adapters are considered only after repeated adoption
friction. Existing consumers remain independent objects: do not rename their
archives, normalize their playbooks, or upgrade their local project versions
to match the MICA tool release.

The version axes remain separate:

- tool release: MICA distribution version
- `mica_spec`: invocation contract version
- project or artifact version: owned by the consumer repository

## Documentation Lifecycle

Current `docs/` contains only:

- this product boundary
- active consumer authoring and adoption guides
- the current release notes
- active PCT, HND, and IVC specifications
- narrowly scoped evidence snapshots that state their revision and authority

Historical release notes, migration guides, declarations, and superseded plans
remain recoverable from Git history and versioned tags. Release summaries also
remain on GitHub Releases and in the changelog. Do not create `docs/legacy`,
`docs/archive`, or `docs/drafts`; those directories previously allowed retired
directions to re-enter the active product surface.
