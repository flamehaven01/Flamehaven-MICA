# Ghost / Files-First / MICA — Three-Layer Comparison

Status:
- reference note
- intended to prevent category confusion
- focuses on architectural role, not product preference

---

## 1. The Core Distinction

These three things do **not** primarily compete on the same layer.

- `Ghost` is a **workspace substrate**
- `files-first memory` is also a **workspace substrate**
- `MICA` is a **memory governance / invocation protocol**

This is the most important framing rule.

If they are compared as if all three are “memory systems” at the same layer, the comparison becomes misleading.

---

## 2. What Each One Actually Solves

### Ghost

Ghost solves:

- where agents store working state
- where agents search
- where agents keep files
- where agents execute safely
- how agents fork and discard experimental state

Its mental model is:

`forkable workspace substrate`

This is why Ghost is best understood as agent infrastructure, not just memory tooling.

### Files-First Memory

Files-first solves:

- readable persistent memory
- simple versioning through Git
- debuggable history through file diffs and blame
- low overhead for single-agent or personal systems

Its mental model is:

`minimum viable memory substrate`

This is strongest when:

- the scale is small
- the memory surface is human-readable
- auditability matters more than query sophistication

### MICA

MICA solves:

- what should count as memory
- how memory is packaged
- when memory should be invoked
- how project identity and invariants are preserved
- how memory drift is recognized
- how lessons and context survive across sessions

Its mental model is:

`portable memory constitution`

MICA is not the storage engine.
It is the protocol that governs how project memory is recognized, loaded, and maintained.

---

## 3. Layer Model

The cleanest architecture is:

1. `workspace substrate`
2. `memory governance`
3. `agent/model execution`

In that model:

- `Ghost` can occupy layer 1
- `files + git + grep` can also occupy layer 1
- `MICA` occupies layer 2

That means:

- Ghost and files-first are alternative substrate strategies
- MICA is an upper-layer protocol that can sit on top of either one

---

## 4. Comparative Roles

| System | Primary layer | Strongest benefit | Main weakness |
|---|---|---|---|
| `Ghost` | workspace substrate | forkable, queryable, multi-agent-friendly infrastructure | can be overbuilt for small personal systems |
| `files-first` | workspace substrate | readability, git auditability, low overhead | weaker coordination and structured multi-agent state handling |
| `MICA` | memory governance | invocation discipline, invariants, portable project memory | no runtime enforcement by itself |

---

## 5. Where Ghost Is Strongest

Ghost is strongest when the project needs:

- multiple agents
- shared state
- queryable temporal memory
- search integrated with storage
- fork-before-risk experimentation
- sandboxed execution tied to the same substrate

In that regime, Ghost is compelling because it reduces glue code across several infrastructure layers.

---

## 6. Where Files-First Is Strongest

Files-first is strongest when the project needs:

- human-readable memory
- Git-native auditability
- very low operational overhead
- personal or single-agent scale
- easy manual correction of bad memory

In that regime, files are not merely “good enough.”
They may be structurally better than a database-backed approach.

---

## 7. Where MICA Is Strongest

MICA is strongest when the problem is not:

- where to store memory

but rather:

- what should be remembered
- how the memory package should be recognized
- what the AI must load first
- how project invariants should constrain behavior
- how drift, lessons, and cycle memory should be handled

That is why MICA belongs above the substrate layer.

---

## 8. Why Ghost and MICA Are Compatible

Ghost and MICA fit together naturally if their boundaries are respected.

Recommended split:

- `Ghost` = storage, retrieval primitives, files, execution context
- `MICA` = admission, invocation, drift discipline, invariant preservation, cycle memory packaging

Ghost answers:

`where does the memory live?`

MICA answers:

`which parts of memory should matter right now, and under what rules?`

This is an additive stack, not a replacement relationship.

---

## 9. Why Files-First and MICA Are Also Compatible

MICA does not require Postgres.

It only requires that project memory exist in inspectable files and that an AI session can read and honor the package.

That means a files-first system can still benefit from MICA:

- `mica.yaml` as composition contract
- archive JSON as project memory anchor
- playbook as operating procedure
- optional drift / lineage / track / result discipline

So the true comparison is not:

`Ghost vs MICA`

but:

`Ghost or files-first as substrate, with or without MICA as governance`

---

## 10. The Most Important Boundary

The main architectural risk is category collapse.

### Risk A: treating Ghost as if it already solves invocation governance

Ghost may store and retrieve memory extremely well.
That does not automatically decide:

- what must be loaded
- what is stale
- what is authoritative
- what should be blocked

### Risk B: treating MICA as if it should become a storage engine

MICA becomes weaker if it tries to absorb:

- execution substrate
- database lifecycle
- search infrastructure
- full runtime policy orchestration

MICA should remain thin enough to sit on different substrates.

---

## 11. Practical Reading Rule

Use the following rule when evaluating any “agent memory” system:

1. Ask whether it is primarily a **substrate**
2. Ask whether it is primarily a **governance protocol**
3. Ask whether it can be layered without collapsing boundaries

Applied here:

- Ghost → substrate
- files-first → substrate
- MICA → governance protocol

That is the clean comparison.

---

## 12. Final Judgment

`Ghost` is a strong substrate story for scalable or multi-agent systems.

`files-first` is a strong substrate story for personal or low-overhead systems.

`MICA` is not best understood as a third substrate.
It is best understood as the portable governance layer that can sit above either one.

In short:

- Ghost gives agents somewhere to work
- files-first gives agents something simple and readable to remember in
- MICA gives the project a constitution for how that memory should be recognized, invoked, and preserved
