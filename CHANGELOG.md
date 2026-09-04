# MICA Changelog

Most recent first. Release notes and migration guides live in [docs/](docs/).

---

## Unreleased

**The measurement tool disagreed with the check it reports on.** `_spec_note`
read `PCT-006`'s own output rather than recomputing a second opinion, then
filtered that output on the substring `canonical`. v3.0.2 rewrote `PCT-006`
around supported contracts and the word disappeared, so a package the check
warns about recorded `spec_note: null`. A `0.2.10` package showed
`PCT-006 [WARN]` and a null note in the same run.

Matching on wording is a second opinion in a smaller place: every rewording
silently drops a warning. There is no filter now. The tool also described itself
as measuring `mica_spec lag`, which stopped being what `PCT-006` does.

The first fix was still not "every warning". `PCT-006` can warn twice in one
run -- a yaml/archive drift and an unknown contract are separate findings about
the same package -- and the function returned on the first, so a package with
both recorded only the drift. `_spec_notes()` returns all of them in order, JSON
gains `spec_notes`, and the human report prints each. `spec_note` remains as the
first element for readers written against it, with a test recording that it can
hide a second warning.

Regression cases cover supported, legacy, unknown, mismatch, and both at once,
asserting the recorded notes are character-for-character and in the same order
as the check's own. One existing test carried the same `canonical` filter the
tool did: once the wording changed both sides went empty and it asserted
nothing while still passing. It reads the check's warnings directly now.

**Published version tags are immutable.** A tag ruleset on `refs/tags/v*` blocks
updates and deletions, with no bypass actor; creating a new version tag is
unaffected. This is the rule that matches what the project already said in
prose: `v3.0.0` was deliberately left carrying superseded documents rather than
moved, because a public tag that changes gives one person something different
from another. Branch protection does not cover tags, and this repository moved a
published tag once before the rule existed.

**`main` accepts only tested commits.** Required status checks are the five CI
jobs, strict, with force-push and deletion refused and no admin bypass. Reviews
are not required: there is no second reviewer to wait for.

Required checks are evaluated against a commit SHA, so CI now runs on every
branch push rather than only on `main`. Without that the arrangement is
circular -- the push that would run the checks is the push those checks gate.
The working shape is unchanged otherwise: push a candidate to a branch, watch
it go green, fast-forward that same SHA onto `main`. Linear history is required,
so the commit messages this project uses as a record survive.

Verified in order rather than assumed: the tag rule was proved by a refused
force-push before anything else was enabled, the five checks were confirmed to
attach to a SHA on a non-`main` branch, and protection was switched on *before*
the first fast-forward so that the fast-forward was the actual test.

---

## v3.0.2 — Contract versions separated from tool versions (2026-09-04)

`PCT-006` measured how far a package's `mica_spec` sat from the tool's own
release number and recommended closing the gap. Both halves were wrong.

The tool release and the contract a package declares are different axes. When
the tools reached 3.x, every consumer read as "at least one major version
behind" while nothing about their packages had changed: six permanent warnings
carrying no information about whether the tools understand those packages. And
MICA does not push consumers toward one version, so a check that reported a gap
and recommended closing it contradicted the project's own position.


**`PCT-006` answers whether the tools define a contract, not how old it is.**

The check measured distance from the tool's own version and suggested closing
the gap. Two things were wrong. The tool release and the contract a package
declares are different axes, so when the tools reached 3.x every consumer read
as "at least one major version behind" while nothing about their packages had
changed -- six permanent warnings carrying no information. And MICA does not
push consumers toward one version, so a check that reported a gap and
recommended closing it contradicted the project's own position.

The version axes are now separate: `MICA_TOOL_VERSION` is `3.0.1`,
`MICA_CONTRACT_VERSION` is `0.2.9`, and `SUPPORTED_CONTRACT_VERSIONS`
enumerates `0.2.4` through `0.2.9`. `0.1.9` is legacy-resolvable. The set is
enumerated rather than bounded because an open range such as `< 4.0` would
claim support for contracts nobody has designed -- `0.2.10` and every future
`3.x` included.

| Declared `mica_spec` | Verdict |
|---|---|
| a supported contract | `PASS mica_spec aligned`; no compatibility warning added |
| `0.1.9` | `INFO`, legacy-resolvable, full support not claimed |
| an undefined version | `WARN`, not a contract these tools define |
| malformed | `WARN` |
| `mica.yaml` and archive disagree | `WARN`, unchanged |

Feature-level incompatibility is not guessed here. The schema and the specific
check that depends on a feature decide that.

Golden output loses 135 lines and gains none: the compatibility warning is
gone for every package on a supported contract. `PCT-006` still reports
`PASS mica_spec aligned` as it always did.

**The spec ratchet covers every check family.** It collected `PCT-\d{3}` only,
so the entire `HND` and `IVC` families -- 13 checks -- sat outside it. `HND-005`
and `IVC-006` were then added in v3.0.1 with no spec and nothing failed, which is
exactly the promise the gate makes. It now collects all three families, and a
further test asserts no family the tools emit is missing from the list it
collects.

Specs written for `HND-005` and `IVC-006` rather than filing them in the
backlog: the backlog is for checks that predate the practice, not for new ones.
30 checks emitted, 7 with a spec, 23 frozen.

The README said "five of seventeen shipping checks" where the real figure was
seven of thirty. Its counts are now asserted against the code, because a number
written by hand in prose drifts the moment either side moves.

`docs/MICA_v3.0.1_RELEASE_NOTES.md` added. The GitHub release body already
carried this content; what was missing was a copy that lives in the repository
and survives independent of the release page. The README document map points at
it.

---

## v3.0.1 — Second invocation-truth audit (2026-09-04)

A second audit falsified the same claim the first one did, by a path the first
fix did not cover. All seven findings reproduced before anything changed. Two of
them only after correcting the counter-example itself, which had been written
against a layer form the fixtures do not use: the findings were right, the first
attempt to reproduce them was not.

The `v3.0.0` tag is unchanged. It is public, and moving a published tag would
make anyone who already fetched it hold something different from anyone who
fetches it later.

**Selection is a request.** `required: false` exempts a layer from being
verified by default, and it was also exempting one the active profile had named:
`PCT-003` passed while the runtime reported the surface missing. A surface a
profile selects must now resolve to a readable file whatever the layer's default
says. An optional layer no profile selected stays exempt.

**The shipped schemas are applied.** `IVC-000` and `HND-000` confirmed a schema
file was on disk and nothing validated against it, so a trace carrying a field
the schema forbids was reported VALID, and a handoff with an empty
`project_scope` passed every hand-written check and reached agent context.
Publishing a schema without applying it is worse than publishing none, because
the schema reads as the contract. `jsonschema` stays optional for vendored
`tools/`, and its absence is reported rather than silently passing.

**One function decides handoff delivery.** There were two implementations, one
for the contract verdict and one for delivery, and fixing the first left the
second wrong. That duplication was introduced by the previous hotfix.

**A trace is validated before it is written.** The record used to be appended
first and checked afterwards: a run could print `Trace: invalid`, leave that
record in the file, and exit 0. The schema alone was not enough, since two roles
pointing at one file is valid JSON and an incoherent capsule, so the writer runs
the same capsule checks the standalone validator runs.

**The consumer guides describe the contract the code implements.** All three
told an external loader to take every `loading_hint: always` layer without
mentioning profiles at all. A consumer AI following them loads more context than
the package intends, and it looks correct while doing it.

**The CI fixture step is a gate again.** It swallowed every failure with
`|| true`, so a traceback and a clean INCOMPLETE were indistinguishable. Negative
fixtures mean it cannot require exit 0, so it now separates an expected contract
failure from a crash.

Corrected in `v3.0.0`'s entry: it said 330 tests where the tag's CI and the
release body both say 333, and the README asserted a single archive filename
pattern most fixtures do not use.

354 tests. Python 3.9, 3.11, 3.12, 3.13.

---

## v3.0.0 — First public release (2026-09-04)

MICA is an invocation and context-loading contract: it decides which memory
surfaces a session receives, and it proves what actually arrived. Everything
before this tag was internal development across roughly three months. This is
the first version published as open source, and the first that carries a
licence.

### What the contract covers

**Selection.** `invocation_protocol.profiles` declares which surfaces a session
gets. A review session and a routine session need not be handed the same memory.
Until this line of work, selection was two hardcoded lists keyed on `mode` while
roughly 580 lines existed to verify delivery: the half that decides what a
session receives had almost no code in it.

A profile may also select sections of a markdown surface, so a playbook is
addressable rather than an opaque file. The capsule digest then covers the
delivered slice rather than the file it came from — hashing a whole file while
delivering part of it would describe context the session never received.

**Audience.** `agent_context_surfaces` is a ceiling: what may reach the agent at
all. The active profile decides what does. `operator_only_surfaces` names
human-review surfaces that must not reach the agent, and naming one surface in
both lists fails the contract rather than resolving to either.

A package that keeps several playbooks apart names them `playbook-eqa`,
`playbook-bav`. A qualifier after the first hyphen narrows a surface without
moving it to another audience, so `sessions-2024` stays out of agent context
exactly as `sessions` does.

**What was left out.** `deferred_surfaces` names the declared surfaces a session
did not get; `deferred_surfaces_basis` says which rule left each one out and what
the surface itself declared. This is not evidence that omitting a surface changed
anything. It is what such a question would need later, instead of only a name.

**Verification.** Digest-bound invocation capsules record what was delivered, by
sha256 over the delivered bytes. `trust_tier: native | attested | opaque` is the
single trust vocabulary, reused by observations, candidates, memories, and
handoff artifact references rather than reinvented per surface.

**Verdict.** Results report on three axes. Only `Contract` decides
`CLOSED CONTRACT`; `Archive` and `Flow` report without deciding it, so a package
whose memory loads correctly but whose archive carries ungrounded bindings gets
both facts instead of one verdict. `mica_pct.py --strict` widens the exit code to
every axis for consumers that want a single gate.

**Handoff.** A bounded surface carrying what one session could not finish into
the next. It holds references and unresolved items, expires, and cannot promote a
candidate memory — the session writing it produced those candidates, so a
promoting writer would be reviewing its own work.

### What an external audit found, and what changed

An audit run against the pre-release code falsified the claim this project rests
on: that a closed contract means the declared surfaces resolved. It did not,
three separate ways. Every counter-example was reproduced before anything was
changed, and each now has a regression test.

- `PCT-003` skipped any layer whose `path` was not a string, and nothing else in
  the chain looks at files. Deleting `path:` from a required archive made the
  surface invisible rather than unresolvable: every check passed, exit 0, and no
  archive at runtime.
- An empty resolved agent context was refilled with every loaded surface, so a
  package declaring `agent_context_surfaces: []` and `operator_only_surfaces:
  [archive, playbook]` was handed exactly the two surfaces it had marked
  operator-only.
- `HND-*` existed only as a standalone command. An expired handoff and one whose
  hash had been rewritten were both delivered like a valid one, contradicting the
  documented rule to exclude an expired handoff.

Also fixed: duplicate layer roles silently changed which file became the evidence
(a dict overwrite, last declaration winning); `project` and `last_updated` were
required capsule fields sitting outside the capsule hash, so a capsule could
attest to a different project or a fresher archive than the real one; invocation
and handoff ids were second-resolution timestamps that collided; the handoff
validator accepted fields its own schema forbids and crashed on a timezone-less
expiry; and `mica_measure --json` reported success after silently dropping
unreadable roots.

The composition schema had drifted from the runtime badly enough to reject 12 of
22 fixtures and the one live consumer that had adopted profiles. Schema and code
now agree, and a test keeps them that way.

### The project's own rules, turned inward

MICA fails consumer packages for drift between schema, config, and docs. Those
demands now apply to this repository in CI:

- a committed snapshot of what every check says about every fixture under every
  profile it declares, so a change to check logic appears as a reviewable diff
  instead of passing because no test covered that fixture
- the declared canonical version must have a changelog entry
- a shipping check must have a spec; 12 of 17 do not, and they are named in a
  backlog that may shrink and never grow
- every fixture must validate against the shipped schema
- README examples are executed, and must print what the README says they print

### Measured

First profile adoption, on `flamehaven-audit-reports`. It declared eight surfaces
and invoked three; five were domain playbooks marked `on_demand`, 33,326 bytes
that reached no session at all.

| Session | Surfaces | Agent-context bytes | vs load-everything |
|---|---|---|---|
| load-everything control | 7 | 61,525 | — |
| `default` | 3 | 28,199 | −54.2% |
| `eqa` | 5 | 50,321 | −18.2% |
| `bav` | 5 | 44,773 | −27.2% |
| `bsc` | 5 | 47,038 | −23.5% |
| `mf` | 5 | 44,595 | −27.5% |

The four task profiles average 46,682 bytes, 24.1% below the control. That is not
a saving against the previous 28,199: it is what makes 33,326 bytes of
declared-but-unreachable memory reachable at all, at a quarter less than loading
it every session.

### What this release does not claim

- It does not measure whether better context produces better work. That needs
  sessions with a control, which has not been run.
- Profile adoption is 1 of 6 live consumer packages.
- No consumer declares a handoff surface yet.
- `PCT-016` is reserved and not implemented.
- Consumer packages declare `mica_spec` from `0.1.9` to `0.2.10`. That spread is
  not a defect to be closed: each package carries its own memory in its own form
  and evolves on its own track. `PCT-006` reports the gap and does not prescribe
  convergence.

333 tests at the v3.0.0 tag. Python 3.9, 3.11, 3.12, 3.13.

---

## Pre-release development (v0.2.0 – v0.2.11, internal)

Not published. Kept here because the release above is the end of this line, not
a fresh start, and because several decisions only make sense with their history.

**Packaging and checks.** `v0.2.0` established the `mica.yaml` composition
contract and the archive/playbook dual-layer model. `v0.2.1`–`v0.2.3` added
portable path layering, `invocation_protocol.primary_pattern`, and the
hook-trigger surface. `v0.2.4` introduced DI binding truth checks (`PCT-010`,
`PCT-011`) without breaking older archives, and `v0.2.5` made `mica_pct.py` and
`mica_runtime.py` delegate to one judgment function so validator and runtime
could not disagree.

**Escalation and stabilisation.** `v0.2.6` added the first opt-in hard fail, for
unbound critical invariants. `v0.2.7` formalised `COMPACT_MODE` and
`di_policy.namespace_mode`. `v0.2.8` added four new signals, all WARN or INFO, so
no existing package broke.

**The invocation-first reset.** Three milestone tags, none of them releases:
`v3.0.0-declaration` froze the repository at an invocation-first floor;
`v3.0.0-invocation-truth` made runtime output stop claiming that an AI had loaded
context and report what was actually resolved; `v3.0.0-origin` reclaimed the
invocation contract from the governance machinery that had grown over it, and
built the selection half that was missing.

**Selection and adoption.** `v0.2.9` shipped memory profiles, addressable
playbook sections, and evidence bound to the delivered slice, and said plainly
that nothing used them. `v0.2.10` was the first consumer adopting them, and the
three defects that trying to adopt exposed. `v0.2.11` was the audit hotfix,
folded into the release above.

Per-version approval notes, changelogs, and migration guides for those
versions are not published. They are internal records for releases nobody
outside the project saw, and the summary above is what they decided.
