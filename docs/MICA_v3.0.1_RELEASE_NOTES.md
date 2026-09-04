# MICA v3.0.1 — Release Notes

**2026-09-04. A second invocation-truth audit, closed.**

`v3.0.0` published the first version anyone outside the project could adopt. An
audit run against it falsified the same claim the pre-release audit had —
that a closed contract means the declared surfaces resolved — by a path the
first fix did not cover.

All seven findings reproduced before anything changed. Two of them only after
correcting the counter-example itself, which had been written against a layer
form the fixtures do not use. The findings were right; the first attempt to
reproduce them was not.

**The `v3.0.0` tag is unchanged.** It is public, and moving a published tag
would make anyone who already fetched it hold something different from anyone
who fetches it later. See [Known limits](#known-limits) for what that leaves in
the `v3.0.0` archive.

---

## What changed

### Selection is a request

`required: false` exempts a layer from being verified by default. It was also
exempting one the active profile had named, so `PCT-003` passed while the
runtime reported the surface missing.

A surface a profile selects must now resolve to a readable file whatever the
layer's default says. An optional layer that no profile selected stays exempt,
and a test pins that so the tightening does not turn every optional layer
mandatory.

### The shipped schemas are applied

`IVC-000` and `HND-000` confirmed a schema file was on disk. Nothing validated
against it. So a trace carrying a field the schema forbids was reported `VALID`
with exit 0, and a handoff with an empty `project_scope` — invalid per the
shipped schema — passed every hand-written check and reached agent context.

Publishing a schema without applying it is worse than publishing none, because
the schema reads as the contract to anyone who finds it. Two checks now apply
it: [`HND-005`](HND-005_v3.0.1_SPEC.md) and [`IVC-006`](IVC-006_v3.0.1_SPEC.md).

`jsonschema` stays optional, because `tools/` is vendored by consumers. Its
absence is reported as `SKIP` with the reason, never as `PASS`.

### One function decides handoff delivery

There were two implementations, one for the contract verdict and one for
delivery, and fixing the first left the second wrong. That duplication was
introduced by the previous hotfix. A test asserts both callers reach the same
function.

### A trace is validated before it is written

The record used to be appended first and checked afterwards, so a run could
print `Trace: invalid`, leave that record in the file, and exit 0. A trace is
provenance; writing one already known to be invalid puts a false account of a
session into the permanent record.

The schema alone was not enough — two roles pointing at one file is valid JSON
and an incoherent capsule — so the writer runs the same capsule checks the
standalone validator runs.

### The guides describe the contract the code implements

All three consumer documents told an external loader to take every
`loading_hint: always` layer, without mentioning profiles at all. A consumer AI
following them loads more context than the package intends, and it looks correct
while doing it.

Profile-first precedence is explicit in each now, and a test asserts the profile
rule appears before the `always` instruction.

### The CI fixture step is a gate again

It swallowed every failure with `|| true`, so a traceback and a clean
`INCOMPLETE` were indistinguishable. Negative fixtures mean it cannot require
exit 0, so it separates an expected contract failure from a crash.

### The spec ratchet covers every family

It collected `PCT-\d{3}` only, so the entire `HND` and `IVC` families — 13
checks — sat outside it. `HND-005` and `IVC-006` were then added with no spec
and nothing failed, which is precisely the promise the gate makes.

It now collects all three families, and a further test asserts that no family
the tools emit is missing from the list the gate collects.

| | Count |
|---|---|
| Checks emitted (`PCT` + `HND` + `IVC`) | 30 |
| With a spec | 7 |
| Frozen in `SPEC_BACKLOG` | 23 |

The README's stated counts are asserted against the code rather than written by
hand, because "five of seventeen" had already drifted from a real thirty.

### Corrected in the v3.0.0 entry

The changelog said 330 tests where the tag's CI and the release body both say
333. The README asserted a single archive filename pattern that most fixtures do
not use; `mica.yaml` names the path, so the README says that and names the
recommended default.

---

## Compatibility

Packages written against `0.2.x` continue to resolve. Two behaviours changed in
ways a package can notice, both from `v3.0.0`:

- a required layer with no usable `path` fails `PCT-003`
- an empty `agent_context_surfaces` no longer falls back to every loaded surface

New in `v3.0.1`: a surface an active profile names must resolve even when its
layer declares `required: false`. A package relying on that being skipped was
not resolving that surface in the first place.

`PCT-006` reports every `0.2.x` package as at least one major version behind
canonical. That is a report, not a requirement — and see below.

---

## Known limits

| Item | State |
|---|---|
| Whether better context produces better work | Not measured. Needs sessions with a control |
| Profile adoption across live consumers | 1 of 6 |
| Handoff surface | Implemented; no consumer declares one |
| Spec coverage | 7 of 30 checks |
| `PCT-016` | Reserved, not implemented |
| `PCT-006` design | Warns on distance from canonical, which now fires on every consumer permanently. Warning on departure from a *supported contract range* would fit consumer autonomy better. Not yet redesigned |
| The `v3.0.0` archive | Still contains 26 internal documents and absolute paths from one developer machine. Removed in `v3.0.1`; the published `v3.0.0` tarball is unchanged because the tag was not moved |
| Release provenance | Tag unsigned. No release asset, checksum, SBOM, branch protection, or tag-triggered release workflow. This is a verified GitHub source release, not a package-registry or CD deployment |

---

354 tests at the v3.0.1 tag. Python 3.9, 3.11, 3.12, 3.13. MIT.
