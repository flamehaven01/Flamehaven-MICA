<p align="center">
  <img src="https://raw.githubusercontent.com/flamehaven01/Flamehaven-MICA/main/docs/assets/mica-logo.png" alt="MICA -- Memory Invocation &amp; Context Archive" width="520"/>
</p>

<p align="center">
  <a href="https://github.com/flamehaven01/Flamehaven-MICA/actions/workflows/ci.yml"><img src="https://github.com/flamehaven01/Flamehaven-MICA/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"/></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"/></a>
  <img src="https://img.shields.io/badge/release-v3.0.1-green.svg" alt="v3.0.1"/>
</p>

<p align="center"><b>Decide which memory a session receives, then prove it received it.</b></p>

<p align="center">
A portable contract for loading project memory at session start and declaring, in bytes, what actually arrived.<br/>
<b>No service &middot; no API key &middot; plain YAML, JSON, and Markdown your team already reads.</b>
</p>

**Release**

- `v3.0.1` — current. Closes a second invocation-truth audit; see the [changelog](CHANGELOG.md).
- `v3.0.0` — the first public release. Everything before it was internal development.
- Adoption is 1 of 6 live consumer packages. Whether better context produces better work is not measured.
- The next step is not more MICA-internal expansion. It is helping other repositories consume the invocation contract cleanly.

---

**Navigation:**
[What It Is](#what-mica-is) •
[60-Second Run](#60-second-first-run) •
[Two Halves](#invocation-has-two-halves) •
[Verdict Axes](#three-axes-one-verdict) •
[Package Surface](#package-surface) •
[Deployment Modes](#deployment-modes) •
[Verification](#verification-path) •
[Document Map](#document-map) •
[Changelog](CHANGELOG.md)

---

## What MICA is

MICA is an invocation and context-loading contract. Its job is to make sure the
right memory surfaces are loaded when a session starts, that the session
activates against the right invariants, and that runtime output says truthfully
what was actually invoked.

It is a memory book with rules about how the book is opened. The archive,
playbook, and memory-first machinery exist to serve that. They are not the
center of the system, and MICA does not sit above the repositories that use it:
each consumer keeps its own package in its own form and evolves on its own
track.

**What it does not do.** It does not prove the code is correct, it does not
measure whether better context produces better work, and it does not decide
anything for you at runtime. It records what was selected and what was
delivered, so those questions can be asked with evidence instead of memory.

---

## 60-Second First Run

Point it at any directory. No configuration needed to get a verdict.

```bash
git clone https://github.com/flamehaven01/Flamehaven-MICA.git
cd Flamehaven-MICA
pip install -r requirements-dev.txt
```

A package that resolves cleanly ends with:

```text
python tools/mica_pct.py fixtures/flow_observation_valid

Contract : CLOSED
Archive  : OK
Flow     : OK

Overall: CLOSED CONTRACT
```

`Contract` is the verdict that matters: the declared memory reached the session
and nothing reached it that should not have. `Archive` and `Flow` report without
deciding it, so a package whose memory loads correctly but whose archive carries
ungrounded bindings gets both facts rather than one verdict. See what a session
actually costs:

```text
python tools/mica_measure.py fixtures/memory_profiles

PACKAGE                     SPEC   CONTRACT   CTX BYTES  CTX/DECL  PROFILES
memory-profiles            0.2.8     CLOSED       1,375       2/3         3
```

## Quick Start

```bash
# Validate a package
python tools/mica_pct.py [project_root]
python tools/mica_pct.py [project_root] --profile review   # under one profile
python tools/mica_pct.py [project_root] --strict           # exit on any axis

# Runtime summary
python tools/mica_runtime.py [project_root] --format text
python tools/mica_runtime.py [project_root] --format hook

# Context budget, in numbers
python tools/mica_measure.py [project_root]

# Handoff surface: bounded state carried to the next session
python tools/mica_handoff.py [project_root]

# Invocation trace provenance
python tools/mica_invocation.py [trace_file_or_project_root]

# Memory-first utility
python tools/mica_memory.py [project_root] paths
python tools/mica_memory.py [project_root] dump slots
python tools/mica_memory.py [project_root] materialize    # synthesize + export + rebuild
```

---

## Invocation has two halves

Deciding which memory a session receives, and proving it received it. MICA once
had roughly 580 lines for the second half and two hardcoded lists for the first.
Selection is now declared:

```yaml
invocation_protocol:
  primary_pattern: readme_protocol
  profiles:
    default:
      surfaces: [archive, playbook]
    review:
      surfaces: [archive, playbook, lessons]
```

```bash
python tools/mica_runtime.py . --profile review
```

A profile names the surfaces that session needs, so a review session and a
routine session need not be handed the same memory. Requesting an undeclared
profile, or naming a surface that is not a declared layer, fails the contract.
Packages that declare no profiles fall back to the mode defaults and resolve
exactly as before.

**The playbook is addressable.** A profile may select sections of a markdown
surface rather than the whole file:

```yaml
    incident:
      surfaces: [archive, playbook]
      sections:
        playbook: [Incident Runbook]
```

An incident session receives the runbook without the review procedure. The
capsule digest then covers the delivered slice, not the file it came from:
hashing a whole file while delivering part of it would describe context the
session never received. Drift is scoped the same way, so editing a section the
profile did not deliver is not drift.

**Specialised surfaces.** A package that keeps several playbooks apart names
them `playbook-eqa`, `playbook-bav`. Those are distinct surfaces when a profile
selects one, and playbooks when MICA decides who may receive them. A qualifier
after the first hyphen narrows a surface without moving it to another audience,
so `sessions-2024` stays out of agent context exactly as `sessions` does.

**The ceiling and the selection.** `agent_context_surfaces` is a ceiling, what
may reach the agent at all. The active profile decides what does. A permitted
surface the profile did not select is deselected, not missing. Without profiles
the two are the same thing, so an uninvoked permitted surface still fails the
contract there.

**What was left out, and why.** `deferred_surfaces` names the declared surfaces
this session did not get. `deferred_surfaces_basis` says which rule did the
leaving out, whether the profile did not name it, an explicit `loading_hint`
never fired, or the mode default does not reach that far, plus what the surface
itself declared. This is not evidence that omitting a surface changed anything.
That question needs a session with a control. It is what such a question would
need later, instead of only a name.

---

## Three axes, one verdict

| Axis | Question | Checks |
|---|---|---|
| `Contract` | Did the declared memory reach this session, and did anything reach it that should not have? | PCT-001/002/003/004/007/008/017 |
| `Archive` | Is the memory content well formed? | PCT-005/006/010/011/012 |
| `Flow` | Is the memory-authoring pipeline coherent? | PCT-013/014/015/018 |

Only the contract axis decides `CLOSED CONTRACT`. A package whose memory loads
correctly but whose archive carries ungrounded bindings has a closed contract
and a failing archive axis, and both are reported. `mica_pct.py --strict` widens
the exit code to every axis for consumers that want a single gate.

`PCT-009` is emitted but belongs to no axis: it restates which contract checks
failed, and counting a summary on an axis would fail that axis twice for one
defect. `PCT-016` is reserved and not implemented.

**Contract versions are not tool versions.** A package declares its contract in
`mica_spec`. `PCT-006` asks whether these tools define that contract, not how
far it is from the tool's own release number:

| Declared `mica_spec` | Verdict |
|---|---|
| `0.2.4`–`0.2.9` | supported; nothing reported |
| `0.1.9` | `INFO`, legacy-resolvable — read, but full support not claimed |
| anything else, including `3.0.1` | `WARN`, not a contract these tools define |

The supported set is enumerated rather than bounded. An open range like
`< 4.0` would claim support for contracts nobody has designed, `0.2.10` and
every future `3.x` among them.

**Runtime reporting.** `MICA CONTRACT RESOLVED` means the declared surface files
were found. `Trace` is separate timestamped invocation provenance and reports
`absent`, `invalid`, `stale`, or `recorded`. `stale` means the recorded capsule
no longer matches the bytes on disk: still a truthful account of a past
invocation, but no longer a description of the current surfaces.

---

## Package surface

Three assets form the minimal package:

| Asset | Format | Role |
|---|---|---|
| `mica.yaml` | YAML | Composition contract: what files exist and how the package is invoked |
| the archive file | JSON | Institutional memory, design invariants, provenance. `mica.yaml` names the path, so any filename works; `memory/mica_archive.json` is the recommended default and older packages use a versioned `*.mica.*.json` form |
| the playbook file | Markdown | Human and AI operating guide. Same rule: `memory/mica_playbook.md` is the recommended default |

Tools:

| File | Role |
|---|---|
| `tools/mica_primitives.py` | Loading, hashing, path canonicalization, markdown sections (no internal deps) |
| `tools/mica_core.py` | Contract resolution, PCT-001..012, verdict axes |
| `tools/mica_evidence.py` | Capsule and invocation-trace validation (`IVC-*`) |
| `tools/mica_flow.py` | Memory-authoring pipeline checks (PCT-013/014/015/017/018) |
| `tools/mica_measure.py` | Context budget and surface resolution, in numbers |
| `tools/mica_handoff.py` | Handoff surface validation (`HND-*`) and writer |
| `tools/mica_pct.py` | Package contract validator |
| `tools/mica_runtime.py` | Portable runtime summary and hook emitter |
| `tools/mica_invocation.py` | Standalone validator for `mica.invocation.jsonl` provenance |
| `tools/mica_memory.py` | Memory-first read/write for sessions, memories, graph edges, slots |

Module layering is acyclic:

```text
mica_primitives          no internal imports
    ^-- mica_evidence    capsule and trace validation
    ^-- mica_flow        memory-authoring pipeline checks
            ^-- mica_core  contract resolution, PCT-001..012, axes
```

`mica_core` re-exports the primitive and evidence names it used to define, so
`from mica_core import ...` keeps working in consumer packages that vendored an
earlier `tools/` copy.

A memory-first package looks like this:

```text
repo/
  mica.yaml
  memory/
    mica.sessions.jsonl
    mica.observe.jsonl
    mica.memories.jsonl
    mica.recall.jsonl
    mica.slots.json
    mica.graph.jsonl
    mica_archive.json
    mica_playbook.md
```

23 fixtures cover the scenarios each check exists for. Full map and expected
output: [fixtures/README.md](fixtures/README.md).

---

## Deployment modes

| Mode | Condition | Verdict |
|---|---|---|
| `INVOCATION_MODE` | `mica.yaml` present | `CLOSED` or `INCOMPLETE` |
| `COMPACT_MODE` | No `mica.yaml`, intentional | `LEGACY` (correct, non-defective) |
| `LEGACY_MODE` | No `mica.yaml`, pre-migration | `LEGACY` (upgrade recommended) |
| `INACTIVE` | Nothing detected | `INACTIVE` |

### DI namespace modes

```yaml
di_policy:
  namespace_mode: domain_namespaced   # or: sequential (default) | legacy_inv
  critical_binding_required: true     # optional: escalates PCT-010 to FAIL
```

| Form | Example | Mode |
|---|---|---|
| `DI-NNN` | `DI-001` | `sequential` (default) |
| `DI-[DOMAIN]-NNN` | `DI-EQA-001`, `DI-BIO-003` | `domain_namespaced` |
| `INV-NNN` | `INV-009` | `legacy_inv` (grandfathered) |

---

## Verification path

The same surface CI runs:

```bash
pip install -r requirements-dev.txt
pytest -v
ruff check tools/ tests/
ruff format --check tools/ tests/
```

Beyond generic linting, CI gates what is specific to MICA:

| Gate | What it catches |
|---|---|
| `tests/test_golden_pct.py` | Any change to what any check says about any fixture, under every profile it declares. Intentional changes regenerate the snapshot and the diff appears in review |
| `tests/test_repo_self_consistency.py` | The declared canonical version with no changelog entry; a shipping check with no spec; a summary check drifting onto an axis |
| `tools/mica_measure.py` | Context budget reported rather than silently drifting |

Regenerate the golden snapshot after an intentional change, and commit it with
the change that caused it:

```bash
python tests/test_golden_pct.py --update
```

Sample check output:

```text
python tools/mica_pct.py fixtures/flow_observation_valid
PCT-013 [PASS] memory/mica.observe.jsonl parseable and hash-chain coherent (2 records)
```

```text
python tools/mica_pct.py fixtures/flow_candidates_broken_provenance
PCT-015 [FAIL] cand_00044: unknown source_event_ids ['obs_missing_999']
Overall: CLOSED CONTRACT
```

That pairing is the axis split working: promotion provenance is broken, and the
invocation contract still closed, because `PCT-015` reports on the flow axis and
only the contract axis decides the verdict.

```text
python tools/mica_runtime.py fixtures/flow_recall_agent_context_violation --format text
Core      : INCOMPLETE
Flow      : FLOW_DEGRADED
Recall    : PASS
Telemetry : PASS
Promotion gate: FAIL
Reason    : candidate cand_00042 entered agent_context while operator_review.state=pending
```

---

## Document Map

By task, not by version.

**Adopting MICA in another repository**

- [docs/MICA_CROSS_REPO_ADOPTION_GUIDE.md](docs/MICA_CROSS_REPO_ADOPTION_GUIDE.md) — making a repository MICA-capable
- [docs/MICA_CONSUMER_AUTHORING_GUIDE.md](docs/MICA_CONSUMER_AUTHORING_GUIDE.md) — authoring and operating a consumer package
- [fixtures/README.md](fixtures/README.md) — every fixture and what it is meant to prove

**Current release**

- [docs/MICA_v3.0.1_RELEASE_NOTES.md](docs/MICA_v3.0.1_RELEASE_NOTES.md) — current: the second audit, what it found, and the known limits that remain
- [docs/MICA_v3.0.0_RELEASE_NOTES.md](docs/MICA_v3.0.0_RELEASE_NOTES.md) — what the first public release was, and what the pre-release audit found
- [CHANGELOG.md](CHANGELOG.md) — v3.0.0, then the internal history it came from
- [docs/MICA_v0.2.9_MIGRATION_GUIDE.md](docs/MICA_v0.2.9_MIGRATION_GUIDE.md) — the last internal migration guide, for packages still on v0.2.8

**Direction and architecture**

- [docs/MICA_v3.0.0_DECLARATION.md](docs/MICA_v3.0.0_DECLARATION.md) — the invocation-first reset and its release boundary
- [docs/MICA_v3.0.0_ORIGIN_RELEASE_NOTES.md](docs/MICA_v3.0.0_ORIGIN_RELEASE_NOTES.md) — Origin P0-P4: what changed, what it measured, what it does not establish
- [docs/MICA_v3.0.0_CONTEXT_CONTINUITY_PLAN.md](docs/MICA_v3.0.0_CONTEXT_CONTINUITY_PLAN.md) — invocation capsule and handoff surface architecture
- [docs/MICA_INVOCATION_RECOVERY_PLAN.md](docs/MICA_INVOCATION_RECOVERY_PLAN.md) — restoring invocation as the primary objective
- [docs/MICA_v0.2.9_MEMORY_FIRST_ARCHITECTURE.md](docs/MICA_v0.2.9_MEMORY_FIRST_ARCHITECTURE.md) — from governed exports to a memory-first substrate
- [docs/MICA_v0.2.9_EVOLUTION_BLUEPRINT.md](docs/MICA_v0.2.9_EVOLUTION_BLUEPRINT.md) — memory flow layer above external memory engines

**Runtime and check specs**

- [docs/MICA_v0.2.9_RUNTIME_STATUS_CONTRACT.md](docs/MICA_v0.2.9_RUNTIME_STATUS_CONTRACT.md) — Core/Flow reporting contract for truthful output
- [docs/PCT-013_v0.2.9_SPEC.md](docs/PCT-013_v0.2.9_SPEC.md) — observation coherence when flow is enabled
- [docs/PCT-014_v0.2.9_SPEC.md](docs/PCT-014_v0.2.9_SPEC.md) — recall trace coverage for active recall surfaces
- [docs/PCT-015_v0.2.9_SPEC.md](docs/PCT-015_v0.2.9_SPEC.md) — promotion provenance for approved lessons
- [docs/PCT-017_v0.2.9_SPEC.md](docs/PCT-017_v0.2.9_SPEC.md) — runtime injection safety for unapproved candidates
- [docs/PCT-018_v0.2.9_SPEC.md](docs/PCT-018_v0.2.9_SPEC.md) — telemetry completeness for joinable flow traces
- [docs/HND-005_v3.0.1_SPEC.md](docs/HND-005_v3.0.1_SPEC.md) — applying the shipped handoff schema, and why it is separate from HND-002
- [docs/IVC-006_v3.0.1_SPEC.md](docs/IVC-006_v3.0.1_SPEC.md) — applying the shipped invocation schema to every capsule in a trace

MICA emits 30 checks across three families: `PCT-*` for the package contract,
`HND-*` for the handoff surface, `IVC-*` for invocation evidence. Of those,
7 have a spec. The other 23 predate the practice and are frozen in
`SPEC_BACKLOG` in `tests/test_repo_self_consistency.py`, which may shrink and
never grow.

That gate only counted `PCT-*` until `v3.0.1`, so the `HND` and `IVC` families
sat outside it entirely and two new checks shipped undocumented without failing
anything. It covers all three families now, and the counts above are asserted
against the code rather than written by hand.

**Schemas**

| Schema | Covers |
|---|---|
| [mica.yaml.schema.json](mica.yaml.schema.json) | The composition contract |
| [mica.invocation.schema.json](mica.invocation.schema.json) | Invocation trace; `v1` history and `v2` digest-bound capsules |
| [mica.handoff.schema.json](mica.handoff.schema.json) | Bounded state carried into the next session |
| [mica-v0.2.7-archive-di-binding.schema.json](mica-v0.2.7-archive-di-binding.schema.json) | Archive DI binding |
| [mica.sessions.schema.json](mica.sessions.schema.json) | Session envelope |
| [mica.observe.schema.json](mica.observe.schema.json) | Observation records |
| [mica.memories.schema.json](mica.memories.schema.json) | Durable memory records |
| [mica.candidates.schema.json](mica.candidates.schema.json) | Candidate registry |
| [mica.recall.schema.json](mica.recall.schema.json) | Recall traces |
| [mica.slots.schema.json](mica.slots.schema.json) | Stable slot projections |
| [mica.graph.schema.json](mica.graph.schema.json) | Memory graph edges |

**Templates and profiles**

Bootstrap templates are in [templates/](templates/), and DI binding and hook
output profiles in [profiles/](profiles/).

Per-version approval notes, changelogs, and migration guides for `v0.2.3`
through `v0.2.8` are not published: they are internal records for versions that
were never released, and the [CHANGELOG](CHANGELOG.md) summarises what they
decided.

---

## License

MIT — see [LICENSE](LICENSE).

<p align="center">
  <b>Flamehaven Initiative</b> •
  <a href="https://github.com/flamehaven01/Flamehaven-MICA/issues">Issues</a> •
  <a href="docs/">Docs</a>
</p>
