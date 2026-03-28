# MICA v0.1.9 / v0.2.0 Evaluation and Flamehaven-TOE Assessment

Status:
- evaluative reference note
- written after `v0.1.9` stabilization and early `v0.2.0` branch creation
- intended as a human + AI orientation document for what MICA is, what it is not, and how to judge it

---

## 1. What MICA Actually Is

`MICA` is not code.

It is not a runtime dependency, not an importable package, and not an execution engine. There is no `import mica`.

`MICA` is an **AI behavior-changing protocol expressed through files**.

When a project contains a valid MICA package:

- `mica.yaml`
- one archive JSON
- one playbook Markdown

an AI that understands the MICA specification can enter `invocation mode`, load the relevant memory surfaces, and follow the declared operating rules.

In that sense, MICA is closer to a **constitution** than to a library.

Its purpose is to solve **session amnesia**:

- AI sessions forget prior project state
- projects accumulate implicit decisions, failed approaches, and invariants
- code history alone does not preserve institutional intent

MICA addresses this by turning project memory into explicit files:

- identity
- canonical statement
- design invariants
- provenance
- self-diagnosis
- lessons

This is not the same thing as version control. Git tracks code change history. MICA tracks **institutional memory and operating discipline**.

---

## 2. What Changed by Version

### v0.1.9

`v0.1.9` is the first version that can reasonably be called a **living standard**.

Its key closure points are:

1. `mica.yaml` composition contract
2. three placement contexts
3. package-level `PCT-*` self-tests
4. archive alignment on the same version axis
5. `README`-driven bootstrap flow

This version solves the earlier problem that MICA packages had no externally legible contract.

### v0.2.0

`v0.2.0` is **not** the new stable core.

It is a **draft branch** for optional profiles derived from stronger control-plane ideas in `ASDP`, while keeping MICA itself a memory layer.

The current branch direction is:

- preserve `v0.1.9` portability
- keep additions optional
- test whether stronger governance-like profiles can be expressed without turning MICA into a full execution architecture

The first active profile candidate is:

- `Approval Profile`

At this stage, `v0.2.0` should be read as a design branch, not as a replacement for `v0.1.9`.

---

## 3. Strengths of the Current Design

### 3.1 Composition Contract

The single most important improvement is the `mica.yaml` composition contract.

It answers a question earlier MICA versions could not answer cleanly:

`What files make this a MICA package?`

This is now machine-checkable through `PCT-*`.

### 3.2 Two Distinct Modes

The split between:

- `memory_injection`
- `protocol_evolution`

is real and useful.

These are not cosmetic labels. They reflect different AI-project interaction patterns:

- periodic maintenance
- iterative experiment cycles

That distinction matters for projects like `Flamehaven-TOE`, where the model or method evolves across repeated dogfood cycles.

### 3.3 Design Invariants with Severity

`design_invariants` are not just notes.

They can express layered force:

- `critical` → block
- `high` → require acknowledgment
- `medium` → warn

That gives MICA a real governance function even though it remains file-based.

### 3.4 Structure Over Assertion

MICA is strongest when it proves things structurally rather than rhetorically:

- `canonical_statement` can be checked against the project
- `provenance_registry` can carry hashes and source links
- `PCT-*` checks package completeness

This aligns well with falsifiability-oriented project design.

---

## 4. Real Limitations

### 4.1 No Runtime Enforcement

MICA only works if the AI reads and follows it.

An AI that does not understand MICA can ignore the files completely.

MICA is therefore not:

- a linter
- a pre-commit hook
- a runtime access control layer

Its force is procedural, not executable.

### 4.2 Archive Weight

The archive JSON remains relatively heavy because the inherited archive schema carries a great deal of design intent.

Some fields describe compilation or reasoning discipline rather than runtime code.

This is not fatal, but it means MICA is partly a **specification-bearing memory format**, not just a lightweight note format.

### 4.3 Bootstrap Is Skeleton-First

At bootstrap time, many important fields begin empty or generic.

Most importantly, `design_invariants` are often initially sparse or empty.

That means a newly inserted MICA package is structurally valid before it is fully institutionally mature.

The package becomes truly alive only after one or more real cycles:

- maintenance cycles
- dogfood cycles
- postmortem lessons

### 4.4 Triggering Is Still Manual

MICA does not auto-detect closure conditions.

Triggers such as:

- `maintenance complete`
- `save MICA`
- `dogfood cycle close`

still depend on a human or AI explicitly treating the cycle as complete.

This is acceptable for a file protocol, but it is still a real limit.

---

## 5. Flamehaven-TOE Specific Assessment

### 5.1 Runtime Impact

For `Flamehaven-TOE`, MICA has effectively **zero runtime impact**.

It does not change:

- `src/`
- `tests/`
- dashboard code
- `pyproject.toml`

MICA adds memory artifacts and a composition contract. It does not alter the execution engine.

### 5.2 Session Efficiency Impact

For a long-lived and conceptually dense project like `Flamehaven-TOE`, the real value is session recovery efficiency.

Without MICA, a new session often has to reconstruct context from:

- `README`
- `CHANGELOG`
- architecture docs
- manual code exploration

With MICA, the AI can recover working orientation from a much smaller set of files:

- `mica.yaml`
- archive `canonical_statement`
- playbook `ontology`
- playbook roadmap
- playbook self-diagnosis

The result is not just token savings. It is **faster convergence on the actual project state**.

### 5.3 Governance Potential

The real TOE value emerges once `design_invariants` are populated.

Examples of strong candidate invariants:

- no arbitrary weighting
- falsifiability-preserving score design
- source hygiene constraints

If these are marked with meaningful severities, MICA becomes a prevention layer against conceptual regression, not just a memory layer.

### 5.4 Lessons as Anti-Pattern Library

In `protocol_evolution` mode, a `lessons/` directory can accumulate failed patterns and recovery paths over repeated cycles.

That gives future sessions something Git does not naturally provide:

- remembered conceptual mistakes
- remembered modeling dead ends
- remembered reasons for rejecting attractive but invalid shortcuts

For a research-heavy project, that is a serious advantage.

---

## 6. Relationship to Existing Systems

MICA should be understood as complementary to other systems, not as a replacement for them.

| System | Scope | Primary role | Relationship to MICA |
|---|---|---|---|
| `CLAUDE.md` at machine/workspace scope | user + workspace | user preferences, workflow hints, tool habits | MICA knows the project; `CLAUDE.md` knows the user/workspace |
| architecture docs | code structure | subsystem explanation | playbook may reference these docs, but does not replace them |
| `CHANGELOG.md` | version history | what changed | MICA explains why it changed and what was learned |
| machine-local auto-memory | machine specific | local accumulated hints | MICA is portable across environments |
| Git history | code change tracking | who changed what | MICA tracks institutional decisions, invariants, provenance, and lessons |

The key distinction is portability.

MICA memory can travel with the project.

That makes it fundamentally different from environment-bound memory systems.

---

## 7. v0.1.9 Judgment

`v0.1.9` should be judged as:

- stable
- portable
- machine-checkable
- operationally meaningful

but still limited by:

- no runtime enforcement
- heavy archive structure
- manual triggers
- maturity depending on real post-bootstrap use

In short:

`v0.1.9` is a strong living standard for memory-layer governance, but not a runtime control system.

---

## 8. v0.2.0 Judgment

`v0.2.0` should be judged as:

- directionally correct
- structurally disciplined
- still draft

Its best current property is restraint:

- optional profiles
- portability preserved
- explicit non-goal of becoming full `ASDP`

Its current limit is equally clear:

- profile ideas exist mostly at spec level
- the first profile candidates still need real dogfood traces
- no profile should be promoted into the stable core before real use demonstrates value

In short:

`v0.2.0` is a controlled design branch, not yet a stabilized standard.

---

## 9. Overall Conclusion

MICA is best understood as a **portable institutional memory protocol for AI projects**.

It does not replace code, runtime controls, or Git. It fills a different gap:

- session continuity
- project identity recovery
- invariant preservation
- provenance anchoring
- lesson carryover across sessions

`v0.1.9` is the first version where that role is genuinely closed as a living standard.

`v0.2.0` is the right next move only if it stays disciplined:

- additive
- optional
- file-based
- memory-first

If it remains within those boundaries, MICA can become stronger without losing the property that makes it valuable in the first place: **portable, readable, project-level memory that changes AI behavior without requiring runtime coupling**.
