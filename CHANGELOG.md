# MICA Changelog

All notable changes per version. Most recent first.
Full release notes and migration guides in `docs/`.

---

## Specialised surfaces and the agent-context ceiling (2026-09-03)

Found while measuring the first consumer against memory profiles. Post-release;
the `v0.2.9` tag does not contain it.

`flamehaven-audit-reports` declares eight surfaces and invokes three. Five of
them are domain playbooks -- `playbook-eqa`, `playbook-bav`, `playbook-bsc`,
`playbook-mf`, `playbook-common`, 33,326 bytes -- marked `on_demand` and
therefore reaching no session at all. Profiles exist for exactly that case, and
two defects stopped the adoption.

### A closed role vocabulary rejected the consumer's own naming

Agent-context eligibility tested a role against six literal names. A package
that keeps several playbooks apart could not deliver any of them: declaring
`playbook-eqa` produced `invalid agent_context surfaces` and an INCOMPLETE
contract. Eligibility now accepts a role whose family -- the segment before the
first hyphen -- is an allowed surface. The audience boundary is unchanged:
`sessions-2024` is still refused agent context, because `sessions` is.

### The ceiling was read as a per-session manifest

`agent_context_surfaces` is global; `profiles` make invocation per-session. A
surface declared once and invoked by one profile therefore failed the contract
under every other profile. `agent_context_surfaces` is now the ceiling and the
profile does the selecting; the difference is reported as
`deselected_agent_context_surfaces` rather than as a broken promise. Packages
without profiles are unaffected -- nothing there explains the gap.

This was already shipped broken. The `handoff_surface` fixture closed its
contract under `resume` and failed under `default` and under no profile at all.
The suite asserted `resume` and reached the rest through `build_summary`, which
never evaluates the contract. The guard added here asserts that profiles do not
decide whether a package's contract holds, and it reproduces the defect when the
fix is reverted.

### Measured

`flamehaven-audit-reports`, agent-context bytes, contract CLOSED throughout:

| Session | Surfaces | Bytes | vs load-everything |
|---|---|---|---|
| load-everything control | 7 | 61,525 | -- |
| `default` | 2 | 28,199 | -54.2% |
| `eqa` | 4 | 50,321 | -18.2% |
| `bav` | 4 | 44,773 | -27.2% |
| `bsc` | 4 | 47,038 | -23.5% |
| `mf` | 4 | 44,595 | -27.5% |

Mean over the four task profiles is 46,682 bytes, 24.1% below the control. This
is not a saving against today's 28,199: it is what makes 33,326 bytes of
declared memory reachable at all, at a quarter less than loading it all every
session. Measured on the package as declared; the consumer's `mica.yaml` is
unchanged pending its owner.

Golden PCT output across 22 fixtures x every declared profile is byte-identical
except the two `handoff_surface` rows that were failing. Tests 224 -> 252.

---

## Handoff surface implemented (2026-09-03)

Closes the one item the v0.2.9 release notes listed as "architecture proposal
only". Post-release addition; the `v0.2.9` tag does not contain it.

A session ends knowing what it produced and what it could not finish. Putting
that in the archive would make unreviewed working state look like project truth;
storing a transcript would move the context problem downstream rather than solve
it. The handoff holds references and unresolved items, nothing more.

- `mica.handoff.schema.json` and `tools/mica_handoff.py` (`HND-000`..`HND-004`)
- `handoff` accepted as a layer `kind` and as an agent-context surface, so it
  flows through the existing profile machinery. No new PCT check: the Context
  Continuity plan defers PCT promotion until a pilot shows a recurring failure
- absence is not a failure; a stale handoff is reported without failing the run
- `handoff_hash` covers everything the record asserts
- a handoff may reference a candidate memory but never promote one. The session
  writing it produced those candidates, so a promoting writer would be reviewing
  its own work
- `state` of `superseded` or `closed`, and an elapsed `expires_at_utc`, keep the
  record visible while marking it not current

### Trust vocabulary: reused, not reinvented

The Context Continuity plan proposed `referenced` / `attested` / `unverified`
for artifact references. The observation schema already ships
`trust_tier: native | attested | opaque`, and the candidates and memories
schemas build `trust_basis` on top of it. A third set of trust words for the
same question would be exactly the drift MICA exists to catch, so artifact
references use `trust_tier`. A test asserts the two enums stay identical.

New fixture `handoff_surface`, new suite `tests/test_handoff_surface.py`.
Tests 203 -> 224.

---

## v0.2.9 - Selection Edition (2026-09-03)

**Stable release.** Supersedes `v0.2.8` as the canonical spec and tool banner.

Promotes the v0.2.9 draft groundwork and the invocation work carried under the
`v3.0.0-*` milestone tags into a release. Those milestone tags stay what they
were -- non-release checkpoints marking direction and implementation, not
superseded by this.

### What ships

- **Three verdict axes.** `Contract` / `Archive` / `Flow`, and only `Contract`
  decides `CLOSED CONTRACT`. Archive quality and pipeline integrity report
  without overriding the invocation contract
- **Memory profiles.** `invocation_protocol.profiles` gives different session
  types different surfaces. Selection was two hardcoded lists keyed on `mode`
- **Addressable playbook.** A profile may deliver named `##` sections; the
  capsule digest covers the delivered slice, not the source file
- **Byte-bound invocation evidence.** `mica.invocation.v2` records path, SHA-256,
  byte count, audience, delivery state, and section slice per surface, under a
  `capsule_hash` that includes the selecting profile
- **Flow plane.** PCT-013/014/015/017/018. PCT-016 reserved for adapter maturity
- **Measurement.** `mica_measure.py` reports context budget, surface resolution,
  and capsule coverage
- **Layered tooling.** `mica_primitives` <- `mica_evidence` / `mica_flow` <-
  `mica_core`, acyclic

### Breaking

`mica_pct.py` exits 1 on a contract failure only. A CI relying on exit 1 for
archive or flow failures -- most commonly `di_policy.critical_binding_required`
escalating PCT-010 -- must add `--strict`. An invalid recorded invocation trace
fails regardless.

### Canonical version

`MICA_CANONICAL_VERSION` is now `0.2.9`, so PCT-006 lag is measured against it.
Packages on `0.2.8` are one patch behind, below the warning threshold. The
version-alignment and lag tests now derive their expectations from the constant
rather than pinning a literal, which is what made them break on this bump.

### Not in this release

Consumer pilot with a control (not run), memory profile adoption (0 / 6 live
consumers), handoff surface (architecture proposal only), fleet `mica_spec`
alignment (0.1.9 - 0.2.10, unresolved).

203 tests on Python 3.9 / 3.11 / 3.12 / 3.13 (202 locally, one skipped on Windows).

-> [MICA_v0.2.9_RELEASE_NOTES.md](docs/MICA_v0.2.9_RELEASE_NOTES.md) | [MICA_v0.2.9_MIGRATION_GUIDE.md](docs/MICA_v0.2.9_MIGRATION_GUIDE.md)

---

## v3.0.0 Origin -- adversarial audit fixes (2026-09-03)

Non-release implementation step. An adversarial pass against the Origin
milestone produced nine findings; all reproduce, all are fixed, and each is now
pinned by a counterexample in `tests/test_adversarial_findings.py`.

### The contract said more than it verified

`PCT-009` reported "declared memory surfaces reached the session" when what it
had established was that the surfaces resolved. Resolution is not delivery. The
message now says `resolved` and points at `IVC-*` for recorded invocation
evidence.

Worse, a corrupted capsule was reported and then ignored: `IVC-004` printed
`FAIL` while `mica_pct.py` exited 0, because the trace checks ran after the exit
code had already been decided. An invalid recorded trace now fails the run.

### Evidence could be forged

`profile` was recorded in the trace but absent from `_CAPSULE_HASH_FIELDS`.
Rewriting `profile: null` to `forged_profile` left the capsule hash unchanged
and passed `IVC-003`/`IVC-004`. The profile decides which memory was selected,
so it is now covered by the hash.

### A surface path only had to exist

`PCT-003` called `.exists()`. A directory at a declared playbook path passed the
contract while producing no evidence for that role, and a path escaping the root
resolved the same way. Declared layer paths must now be readable files inside
the project root.

### Malformed profiles degraded quietly

- `surfaces: []` fell back to the mode defaults, ignoring the operator's request
- `surfaces: [archive, archive]` produced duplicate loaded surfaces and evidence

Both now fail `PCT-007`.

### The validator ignored an argument it was given

`mica_pct.py` stripped `--strict` by hand and dropped everything else, so
`--profile does_not_exist` validated the *default* profile and exited 0. The CLI
uses `argparse` now: `--profile` is honoured and unknown flags are rejected.

### The markdown parser mistook code for structure

`parse_markdown_sections` did not track fences, so a `## heading` inside a
```` ``` ```` block registered as a section and truncated the real one around it.
This broke the P2 guarantee that a delivered slice is the section that was
selected. The parser is fence-aware and handles both backtick and tilde fences.

### Measurement reported coverage it did not have

`identifies_exact_bytes` was `bool(evidence)`, so one digest out of two invoked
surfaces read as full coverage. It now requires a digest for every invoked
surface. `mica_measure.py` also exited 0 after skipping unreadable roots, which
made a partial fleet reading indistinguishable from a complete one; skipped
roots now exit 1.

### A spec with no version number passed

`mica_spec: not-a-version` produced `_parse_version(...) == (0,)` and PCT-006
returned `mica_spec aligned`. It now warns that the value cannot be compared.

### Documented arithmetic did not hold

The P3 verification note said "20 fixtures x 5 profile selections: 105
combinations". 20 x 5 is 100. The count was taken over the 21 fixtures carrying
a `mica.yaml`; the derivation is corrected. The fleet baseline also read as
though every session received 213,112 bytes -- that is the sum across six
consumers, ranging 3,998 to 97,560 each. The invariant is that *within* each
consumer, every task receives the same set.

Tests 184 -> 204.

---

## v3.0.0 Origin P4 - Measurement, and what it found (2026-09-03)

Non-release implementation step. Stable tag and tool banner remain `v0.2.8`.

MICA has had no metrics. Every claim about it has been structural ("the check
fires") rather than quantitative ("the session receives N bytes"). `mica_measure.py`
reports what is deterministically observable at session start: context budget in
bytes, surface resolution, capsule coverage, and verdict axes.

It is a measurement instrument, not a result. It says nothing about whether MICA
improves task outcomes; that needs sessions with a control, which a static scan
cannot supply. The tool prints that caveat itself.

### PCT-006 was stating a number it could not support

Versions were packed as `major*10000 + minor*100 + patch` and the difference
reported as "N version(s) behind". Within one minor that is a true patch count.
Across a minor boundary it counts nothing: a package declaring `0.1.9` was told
it was **99 version(s) behind** canonical `0.2.8`. One of the six live consumer
packages declares `0.1.9`, so the false number was shipping.

- same minor: reports a real patch count
- different minor: names the gap without a number
- ahead of canonical: now a WARN. `Flamehaven-CAS` declares `0.2.10` and the old
  formula produced a negative lag, which fell below the threshold and stayed
  silent. A spec with no canonical schema is worth saying out loud
- `mica_measure.py` reads PCT-006's own message instead of recomputing the
  comparison. Two implementations of one comparison is the drift MICA exists to
  catch, and the first draft of the tool had exactly that

Verified against the golden baseline captured for P3: across 105 (fixture,
profile) combinations, PCT-006 is the only check whose output changed. Every
other result is byte-identical.

### Fleet baseline, six live consumer packages

| Package | mica_spec | Contract | Agent context bytes |
|---|---|---|---|
| alecta-stock | 0.2.6 | CLOSED | 15,893 |
| flamehaven-verification | 0.2.8 | CLOSED | 28,199 |
| flamehaven-cas | 0.2.10 | CLOSED | 3,998 |
| stem-ai-bio | 0.2.4 | CLOSED | 51,056 |
| cocomini-ultimatepos | 0.2.8 | CLOSED | 16,406 |
| flamehaven-space-maintainer | 0.1.9 | CLOSED | 97,560 |

All six close the contract. All six can identify their invoked bytes.
**None declares a memory profile**: P1 and P2 have zero adoption, and the 213,112
bytes above are what every session in the fleet receives regardless of task.

Tests 168 -> 184 (183 pass plus one skipped on Windows, where the symlink
escape test cannot create a link; CI runs it on Linux).

---

## v3.0.0 Origin P3 - Layered modules and decomposed checks (2026-09-03)

Non-release implementation step. Stable tag and tool banner remain `v0.2.8`.

AI-SLOP-DETECTOR v3.8.9 measured `mica_core.py` at 1,893 lines, deficit score
68.2, status `inflated_signal`, with 4 critical and 15 high findings. The worst
single item was `run_pct_checks`: 457 logic lines, cyclomatic complexity 88,
nesting depth 5.

Extracted by concern:

| Module | Contents |
|---|---|
| `mica_primitives.py` | Loading, hashing, path canonicalization, markdown sections. No internal imports |
| `mica_evidence.py` | Capsule schema and coherence, invocation trace checks, live-byte comparison |
| `mica_flow.py` | PCT-013/014/015/017/018 and their helpers |

Extracting flow and evidence first produced two import cycles back into
`mica_core`, which the detector caught (cross-file risk 0.13 -> 0.33). The
primitives layer resolves them; the graph is acyclic.

`run_pct_checks` decomposed: `_PackageContext` resolves package state once, and
PCT-002..012 became `_run_pct002`..`_run_pct012`. PCT-010 and PCT-011 were
separated from one 91-line body. PCT-004's six-branch elif chain became a mode
-> required-roles table. `resolve_invocation_contract` split into surface
selection plus two audience validators.

Extraction alone was not enough, and the detector showed it: lifting the
audience loops into their own functions carried their depth-5 nesting with
them, so both new helpers came out critical. They are now flattened around
`_classify_surface`, which returns a reason instead of appending into one of
several lists.

Behavior verified rather than assumed: a golden baseline of `run_pct_checks`
output was captured before the refactor across the 21 fixtures carrying a
mica.yaml x 5 profile selections -- 105 combinations, 1,840 results -- and
compared after every step.
Identical throughout.

All figures below are AI-SLOP-DETECTOR v3.8.9 output on `tools/`, measured at
this commit. Its line count is logic lines, not raw file lines -- `wc -l` on the
same file reports 1,174, since the detector excludes comment and blank lines.

| Measure | Before | After |
|---|---|---|
| cross-file risk | 0.13 | 0.00 |
| total critical | 5 | 3 |
| `mica_core.py` critical | 4 | 0 |
| `mica_core.py` high | 15 | 4 |
| `mica_core.py` deficit | 68.2 | 29.0 |
| `mica_core.py` status | `inflated_signal` | `clean` |
| `mica_core.py` logic lines | 1,893 | 1,004 |

Total high is unchanged at 23: splitting a large function produces more
functions, several of which still exceed the 50-line threshold on their own.
The three remaining criticals are `_run_pct018`, `_check_capsule_schema`, and
`mica_memory.main` -- none in core.

---

## v3.0.0 Origin P2 - The playbook becomes addressable (2026-09-03)

Non-release implementation step. Stable tag and tool banner remain `v0.2.8`.

MICA is a memory and playbook package, but structurally the playbook was one
opaque file path. The archive had invariants, a schema, and binding provenance;
the playbook had nothing. A profile could load it, but only whole -- an incident
session received the review procedure and the onboarding notes as well.

- `parse_markdown_sections()` and `select_markdown_sections()` split a markdown
  surface into its preamble and `##` sections. The preamble always travels with
  a slice, since sections assume the framing above them
- profiles may declare `sections: {<role>: [names]}`; only surfaces the profile
  invokes may be sliced
- capsule evidence records `sections` and hashes the **delivered slice**. Hashing
  the file while delivering part of it would make the evidence describe content
  the session never received
- drift is scoped to the delivery: editing a section the profile did not deliver
  is not drift; editing or removing a delivered section is
- PCT-007 fails the contract when a profile requests a section that does not
  exist, or selects sections of a surface it does not invoke. Both are the same
  class as an undeclared surface: the session asked for memory the package
  cannot supply
- `rehash_evidence_entry()` added so the write-time re-resolve and IVC-005 share
  one definition of what a capsule covers

Fixed while implementing: `write_invocation_trace` re-hashed the whole file
during its resolve-to-emit check, so recording any sectioned capsule failed with
a false drift error. IVC-005 had already been made slice-aware; the write path
had not. Both now go through `rehash_evidence_entry`.

Fixture `memory_profiles` gains an `incident` profile and a four-section
playbook. Tests 157 -> 168.

---

## v3.0.0 Origin P1 - Memory profiles: the selection half of invocation (2026-09-03)

Non-release implementation step. Stable tag and tool banner remain `v0.2.8`.

Invocation has two halves. MICA had built one of them to ~580 lines -- capsules,
digests, IVC checks, live-byte comparison, all proving that whatever loaded had
loaded. The other half, deciding what should load, was two hardcoded lists:

    ["archive", "playbook", "slots"] if mode == "memory_first" else ["archive", "playbook"]

Every session received the same surfaces regardless of what it was for.

- `invocation_protocol.profiles`: named surface sets. A profile declares which
  layers a session invokes at session start
- `resolve_invocation_contract(yd, profile)` and `run_pct_checks(root, profile)`
  accept a profile; `mica_runtime.py --profile <name>` selects one
- precedence: requested profile, then `loading_hint: session_start` on layers,
  then the mode defaults
- a `default` profile applies when none is requested
- PCT-007 fails the contract when a requested profile is undeclared, or when a
  profile names a surface that is not a declared layer. Both are invocation
  faults: the session asked for memory the package cannot supply
- capsule evidence and `agent_context` follow the profile, so the digests
  recorded for a session cover exactly the surfaces that session selected
- the invocation trace records `profile`; null when no profiles are declared
- `mica_runtime.py --format text` reports the active profile
- new fixture `memory_profiles`; new suite `tests/test_memory_profiles.py`
- tests 143 -> 157

Backward compatible. A package that declares no profiles resolves exactly as it
did before, `active_profile` is null, and no existing fixture changed behavior.

---

## v3.0.0 Origin P0 - Reclaim the invocation contract (2026-09-03)

Non-release implementation step. Stable tag and tool banner remain `v0.2.8`.

MICA is a memory and playbook package, not a governance engine. v3.0.0-declaration
said so in prose, but the code still let archive quality and memory-authoring
integrity break the invocation contract: `HARD_FAIL_CHECKS` contained PCT-010,
PCT-013, and PCT-015, so a package whose memory loaded correctly could be
reported INCOMPLETE because a DI binding was ungrounded or a candidate's
provenance was broken. The declaration demoted governance; it did not remove
its authority. This step removes the authority.

- verdict split into three axes: `CONTRACT_CHECKS`, `ARCHIVE_CHECKS`, `FLOW_CHECKS`
- PCT-010, PCT-013, PCT-015 no longer break the contract; they report on their
  own axis and keep their existing severities, including the opt-in escalation
  from `di_policy.critical_binding_required`
- PCT-017 stays on the contract axis. It asks what entered `agent_context`,
  which is an invocation question, not a governance one -- this corrects an
  earlier misclassification
- PCT-009 narrowed to the contract axis and reworded accordingly
- `evaluate_axes()` and `failing_axes()` added
- `mica_pct.py` prints all three axes; `--strict` widens the exit code beyond
  the contract for consumers that want a single gate
- `HARD_FAIL_CHECKS` kept as a contract-only alias for vendored tool copies
- `tests/test_verdict_axes.py` added: axis disjointness, membership, per-fixture
  behavior, and CLI exit codes. Tests 127 -> 143

Fixture behavior change:

| Fixture | Before | After |
|---|---|---|
| `binding_required_fail` | INCOMPLETE | Contract CLOSED, Archive FAILED |
| `flow_candidates_broken_provenance` | INCOMPLETE | Contract CLOSED, Flow FAILED |
| `flow_recall_agent_context_violation` | INCOMPLETE | unchanged -- PCT-017 is invocation |

Consumers relying on `mica_pct.py` exit 1 for archive or flow failures must add
`--strict`.

---

## v3.0.0 P1 - Digest-bound invocation evidence (2026-09-03)

Non-release implementation step. Stable tag and tool banner remain `v0.2.8`.
Implements P1 of `docs/MICA_v3.0.0_CONTEXT_CONTINUITY_PLAN.md`.

- `mica.invocation.v2`: adds `trigger`, `surface_evidence`, and `capsule_hash`
- `surface_evidence` records canonical repo-relative path, `sha256`, byte count,
  audience, and delivery state for each loaded surface
- delivery states pinned to `declared` / `resolved` / `emitted` / `acknowledged`;
  none of them claims the model read, understood, or obeyed the content
- runtime records `resolved` only -- it hashes bytes, it does not deliver them
- `capsule_hash` excludes the absolute `project_root` so a capsule reproduces
  identically across platforms; field set, ordering, and encoding are pinned
- `write_invocation_trace` re-resolves digests before writing and refuses to
  record a capsule when a surface changed between resolution and emission
- `canonical_surface_path` rejects paths that escape the project root
- v1 records remain valid and are never rewritten; v2 fields stay optional
- new fixture `invocation_capsule_v2` with a byte-bound committed trace
- new suites `tests/test_invocation_capsule_v2.py` and
  `tests/test_schema_metavalidation.py`; tests 62 -> 126

Contract gaps found in review and closed before push:

- the `surface_evidence.path` pattern was not a valid ECMA regex, so the whole
  schema failed Draft 2020-12 metavalidation
- `invocation_id` was lowercase-only while `session_id` in the same schema
  allowed uppercase; every generated id (`inv_<ISO>Z`) and every committed
  fixture trace was therefore invalid against the schema it ships with. This
  predates v2 and was never detected because nothing validated records against
  the schema. The pattern is now aligned; no recorded history was rewritten
- v2 evidence had to be a subset of loaded surfaces but not a complete account,
  so a record could claim a loaded surface while omitting its bytes. Evidence
  must now cover every loaded surface
- the schema left the v2 continuity fields globally optional; they are now
  conditionally required when `schema_version` is `mica.invocation.v2`
- `IVC-005` added: when validating a project root, the newest capsule's digests
  are re-hashed against the bytes on disk. Drift is WARN, not FAIL -- a record
  was true when written, so a later edit makes it stale rather than invalid.
  `mica_invocation.py` now reports `VALID INVOCATION TRACE (stale evidence)`
  and exits 0 for that case
- `jsonschema` added to `requirements-dev.txt`; new suite metavalidates all ten
  shipped schemas and validates real runtime output and every committed trace
  against the invocation schema

Adversarial review found two more, both closed before push:

- `IVC-005` read the path recorded in the trace directly, so a record claiming
  `../outside.txt` caused the validator to hash a file outside the package and
  report PASS while `IVC-003` reported FAIL on the same record. Recorded paths
  are now re-resolved against the root (symlinks included) and refused if they
  escape, and the live-byte check is skipped entirely when `IVC-003` or
  `IVC-004` failed. An unsound record cannot direct the validator at a file
- the runtime passed only the trace file to the validator, so `IVC-005` was
  skipped and a drifted package was reported as `Trace: recorded` while
  `mica_invocation.py <root>` reported stale. The runtime now resolves against
  the project root and reports `absent` / `invalid` / `stale` / `recorded`

The three states stay separate: artifact validity (`IVC-003`/`IVC-004`),
continuity freshness (`IVC-005`), and runtime trace state (`Trace:`). A stale
capsule is a valid artifact whose continuity with current surfaces is broken.

No new PCT was added. Per the plan, PCT promotion waits for a consumer pilot
(P4) that demonstrates a recurring, machine-detectable contract failure.

---

## Consumer adoption note - 2026-07-19

- Added a concrete Cocomini UltimatePOS/StoreAiAssist adoption note.
- Documented the boundary between session-start MICA context, retail-assistant memory/RAG, and live POS truth.
- Recorded status-truth and versioned knowledge-sync practices without changing the stable MICA release or tool banner.

---

## v3.0.0-invocation-truth - Consumer Truthfulness Milestone (2026-07-11)

Non-release implementation milestone. Latest stable release tag and tool banner remain `v0.2.8`.

- PCT-007 distinguishes an absent invocation protocol from an explicit protocol with an omitted `primary_pattern`; the latter is a compatibility WARN that names the `readme_protocol` default
- runtime output reports `MICA CONTRACT RESOLVED`, declared/defaulted pattern source, and absent/recorded/invalid trace evidence instead of claiming that an AI loaded context
- canonical consumer kit added: `MICA_CONSUMER_AUTHORING_GUIDE.md`, `MICA_AGENT_GUIDE.md`, and `mica-consumer-minimal.yaml`
- consumer guidance now covers YAML-driven archive resolution for runtime-backed consumers and the boundary of null-session invocation traces
- `implicit_primary_pattern` fixture and regression coverage added for partial invocation contracts

## v3.0.0-declaration - Invocation-first Floor (2026-07-09)

Milestone tag for freezing the repository at the invocation-first floor.
This is not a stable release; tool banners remain `v0.2.8` until a later versioned release.

Latest stable release tag remains `v0.2.8`.
The current working direction is a frozen invocation-first floor, with subsequent effort expected to move toward cross-repo consumption rather than deeper MICA-internal expansion.

### Declaration

- v3.0.0 direction declared: MICA is being reset around invocation-first context loading, truthful loaded-state declaration, and auditable invocation traces
- v3.0.0 declaration note added: `docs/MICA_v3.0.0_DECLARATION.md`
- README and About wording now place governance and memory-first machinery beneath the primary invocation contract
- obsolete `docs/CAS_AUDIT_PLAYBOOK.md` removed during doc sanity cleanup

### Landed between v0.2.8 and this tag

Stable-release maintenance plus `v0.2.9` draft groundwork. Per the README release table,
`v0.2.9` remains unreleased groundwork and does not change the stable tag or tool banner.

- Tool version banner alignment: `mica_pct.py` and `mica_runtime.py` now report `v0.2.8` consistently
- Legacy archive selection is now deterministic: highest version first, then `operation_meta.last_updated`
- Regression tests expanded: 10 -> 13
- README doc sanity updated: PCT range now includes PCT-012; superseded v0.2.4 root schema link removed
- v0.2.9 design blueprint added: `docs/MICA_v0.2.9_EVOLUTION_BLUEPRINT.md`
- v0.2.9 phased execution plan added: `docs/MICA_v0.2.9_EXECUTION_PLAN.md`
- v0.2.9 schema drafts added: `mica.observe.schema.json`, `mica.candidates.schema.json`, `mica.recall.schema.json`, and flow fixtures
- v0.2.9 flow validator now enforces `PCT-013`, `PCT-015`, and `PCT-017` with runtime `Core` / `Flow` separation
- v0.2.9 PCT spec notes added: `docs/PCT-013_v0.2.9_SPEC.md`, `docs/PCT-014_v0.2.9_SPEC.md`, `docs/PCT-015_v0.2.9_SPEC.md`, `docs/PCT-017_v0.2.9_SPEC.md`, `docs/PCT-018_v0.2.9_SPEC.md`
- v0.2.9 runtime status contract added: `docs/MICA_v0.2.9_RUNTIME_STATUS_CONTRACT.md`
- cross-repo packaging guidance added: `docs/MICA_CROSS_REPO_ADOPTION_GUIDE.md`
- memory-first architecture draft and starter template added: `docs/MICA_v0.2.9_MEMORY_FIRST_ARCHITECTURE.md`, `templates/mica-v0.2.9-memory-first.yaml`
- `mica.yaml.schema.json`, `mica_core.py`, and `mica_runtime.py` now accept `mode: memory_first` plus kind-based export layers
- memory-first record schema drafts added: `mica.sessions.schema.json`, `mica.memories.schema.json`, `mica.slots.schema.json`, `mica.graph.schema.json`
- standalone invocation provenance schema added: `mica.invocation.schema.json` for independently validating `mica.invocation.jsonl` artifacts
- standalone invocation trace validator added: `tools/mica_invocation.py`
- `mica_invocation.py` now reports standalone schema presence and `mica_pct.py` prints `IVC-*` summary when an invocation trace artifact exists
- `tools/mica_memory.py` added: minimal writer/parser utility for memory-first sessions, memories, graph edges, and slots
- `tools/mica_memory.py synthesize-memories` added: deterministic observe -> candidate_memory promotion
- `tools/mica_memory.py refresh-projections` added: deterministic memories -> slots / graph projection rebuild
- `tools/mica_memory.py review-memory` added: deterministic candidate_memory -> approved_lesson / bound_invariant_evidence promotion
- `tools/mica_memory.py export` now materializes archive/playbook surfaces from approved/promoted memories and synthesizes design_invariants from bound evidence
- `tools/mica_memory.py materialize` added: single-command rebuild for observations -> memories -> archive/playbook -> slots/graph
- Repository metadata and docs now reflect the intended v3.0.0 invocation-first reset while `v0.2.9` remains draft groundwork

---

## v0.2.8 - Binding Depth Edition (2026-06-24)

**4 new PCT signals. No existing package breaks. All new signals are WARN or INFO.**

- **PCT-010 doctrinal WARN**: Detects `origin_episode` with no episode code (`EXP-xxx`), version ref, or date - signals ungrounded binding
- **PCT-010 coherence WARN**: `violation_count > 0` with empty `last_triggered` -> data defect
- **PCT-012 new (opt-in)**: `di_policy.max_archive_age_days` in mica.yaml -> WARN when archive is stale
- **PCT-006 version lag**: WARN when `mica_spec` is >= 2 versions behind canonical `0.2.8`
- `_EPISODE_PATTERNS`, `MICA_CANONICAL_VERSION`, `_parse_version()` added to mica_core.py
- `di_policy.max_archive_age_days` added to mica.yaml.schema.json
- 3 new fixtures: `doctrinal_binding`, `stale_archive`, `violation_count_incoherent`
- Tests: 7 -> 10 (all GREEN)

-> [MICA_v0.2.8_CHANGELOG.md](docs/MICA_v0.2.8_CHANGELOG.md) | [MICA_v0.2.8_APPROVAL_NOTE.md](docs/MICA_v0.2.8_APPROVAL_NOTE.md)

---

## v0.2.7 - Frame Stabilization Edition (2026-06-24)

**A small but important compatibility release that stabilizes hook output, LEGACY handling, and policy naming.**

- `COMPACT_MODE` formalized as a first-class deployment interpretation
- `di_policy.namespace_mode` added to `mica.yaml.schema.json`
- `mica_runtime.py` LEGACY and INACTIVE handling clarified; no behavior break
- Hook-output summary format preserved while adding policy forward-compatibility
- Legacy packages remain valid

---

## v0.2.6 - Critical Binding Escalation (2026-06-24)

**First opt-in hard fail for unbound critical invariants.**

- `di_policy.critical_binding_required: true` now escalates unbound critical DIs from WARN to FAIL
- `mica_core.run_pct_checks()` owns that escalation logic so validator and runtime agree
- New fixture: `binding_required_fail`
- Existing packages unchanged unless they opt in

---

## v0.2.5 - Runtime/PCT Unification (2026-06-24)

**Single source of truth for package judgment.**

- `mica_pct.py` and `mica_runtime.py` now both delegate PCT judgment to `mica_core.run_pct_checks()`
- `tools/mica_runtime.py` reports `CLOSED`, `INCOMPLETE`, `LEGACY`, or `INACTIVE` consistently
- Hook-specific coherence warning added when `loading_hint=hook` is used without `hook_trigger`
- Added fixture: `hook_output_violations_only`

---

## v0.2.4 - Archive Binding Contract (2026-06-24)

**Introduced DI binding truth checks without breaking older archives.**

- `PCT-010` added: critical DI binding presence / truth-depth checks
- `PCT-011` added: `binding.lesson_ref` dead-link detection
- Legacy archive structure remains valid when bindings are absent

---

## v0.2.3 - Hook Invocation Surface (2026-06-24)

- `invocation_protocol.hook_output` added
- Hook-trigger invocation pattern stabilized

---

## v0.2.2 - Invocation Protocol (2026-06-24)

- `invocation_protocol.primary_pattern` introduced
- Runtime summary now reports invocation pattern

---

## v0.2.1 - Portable Packaging Pass (2026-06-24)

- Added portable path layering rules in `mica.yaml`
- Strengthened package completeness checks

---

## v0.2.0 - Control Plane Baseline (2026-06-24)

- Initial `mica.yaml` packaging contract
- Archive / playbook dual-layer model
- First PCT family for package closure checks
