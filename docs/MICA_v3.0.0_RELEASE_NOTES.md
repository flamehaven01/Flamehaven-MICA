# MICA v3.0.0 — Release Notes

**2026-09-04. The first public release.**

Everything before this tag was internal development across roughly three months
and eleven `0.2.x` versions. None of it was published. This is the first version
that carries a licence and the first that anyone outside the project can adopt.

The version number is not a maturity claim. It is where the internal work
arrived: `v3.0.0-declaration`, `v3.0.0-invocation-truth`, and `v3.0.0-origin`
were milestone checkpoints on a reset that had already been declared internally,
and this release is that reset finished and published.

---

## What MICA is

An invocation and context-loading contract. It decides which memory surfaces a
session receives, and it proves what actually arrived.

It is a memory book with rules about how the book is opened. It does not sit
above the repositories that use it: each consumer keeps its own package in its
own form and evolves on its own track.

## What it is not

- It does not prove code is correct.
- It does not measure whether better context produces better work.
- It does not decide anything at runtime. It records what was selected and what
  was delivered, so those questions can be asked with evidence.

---

## The contract

### Selection

`invocation_protocol.profiles` declares which surfaces a session gets:

```yaml
invocation_protocol:
  primary_pattern: readme_protocol
  agent_context_surfaces: [archive, playbook, lessons]
  profiles:
    default:
      surfaces: [archive, playbook]
    review:
      surfaces: [archive, playbook, lessons]
    incident:
      surfaces: [archive, playbook]
      sections:
        playbook: [Incident Runbook]
```

An incident session receives the runbook without the review procedure. The
capsule digest then covers the delivered slice rather than the file it came from:
hashing a whole file while delivering part of it would describe context the
session never received. Drift is scoped the same way, so editing a section the
profile did not deliver is not drift.

Until this line of work, selection was two hardcoded lists keyed on `mode`, while
roughly 580 lines existed to verify delivery. The half that decides what a
session receives had almost no code in it.

### Audience

`agent_context_surfaces` is a ceiling — what may reach the agent at all — and the
active profile decides what does. `operator_only_surfaces` names human-review
surfaces that must not reach the agent. Naming one surface in both fails the
contract rather than resolving to either.

A package that keeps several playbooks apart names them `playbook-eqa`,
`playbook-bav`. A qualifier after the first hyphen narrows a surface without
moving it to another audience, so `sessions-2024` stays out of agent context
exactly as `sessions` does.

### What was left out

`deferred_surfaces` names the declared surfaces a session did not get.
`deferred_surfaces_basis` says which rule left each one out — the profile did not
name it, an explicit `loading_hint` never fired, or the mode default does not
reach that far — and what the surface itself declared.

This is not evidence that omitting a surface changed anything. That needs a
session with a control. It is what such a question would need later, instead of
only a name.

### Verdict

| Axis | Question | Checks |
|---|---|---|
| `Contract` | Did the declared memory reach this session, and did anything reach it that should not have? | PCT-001/002/003/004/007/008/017 |
| `Archive` | Is the memory content well formed? | PCT-005/006/010/011/012 |
| `Flow` | Is the memory-authoring pipeline coherent? | PCT-013/014/015/018 |

Only `Contract` decides `CLOSED CONTRACT`. A package whose memory loads correctly
but whose archive carries ungrounded bindings gets both facts rather than one
verdict. `--strict` widens the exit code to every axis.

`PCT-009` is emitted but sits on no axis: it restates which contract checks
failed, and counting a summary on an axis would fail that axis twice for one
defect. `PCT-016` is reserved and not implemented.

### Handoff

A bounded surface carrying what one session could not finish into the next. It
holds references and unresolved items, expires, and cannot promote a candidate
memory — the session writing it produced those candidates, so a promoting writer
would be reviewing its own work. An expired, superseded, or tampered handoff is
withheld from agent context and the contract says so.

---

## What an external audit found

An audit run against the pre-release code falsified the claim this project rests
on: that a closed contract means the declared surfaces resolved. Every
counter-example was reproduced before anything changed, and each has a regression
test.

| Finding | What it meant |
|---|---|
| `PCT-003` skipped layers whose `path` was not a string | Deleting `path:` from a required archive made the surface invisible rather than unresolvable. Every check passed, exit 0, no archive at runtime |
| An empty agent context was refilled with every loaded surface | A package marking archive and playbook operator-only was handed exactly those two |
| `HND-*` was wired to nothing | An expired handoff and one with a rewritten hash were both delivered like a valid one |
| Duplicate layer roles | A dict overwrite, last declaration winning: a decoy file could become the recorded evidence |
| `project` and `last_updated` outside the capsule hash | A capsule could attest to a different project, or a fresher archive than the real one |
| Second-resolution ids | Two invocations or handoffs in the same second shared an id |
| Handoff validator weaker than its schema | Unknown fields accepted; a timezone-less expiry crashed the run |
| `mica_measure --json` | Reported success after silently dropping unreadable roots |
| Schema drift | The shipped composition schema rejected 12 of 22 fixtures and the one live consumer that had adopted profiles |

---

## The project's own rules, turned inward

MICA fails consumer packages for drift between schema, config, and docs. Those
demands now apply to this repository, in CI:

| Gate | What it catches |
|---|---|
| `tests/test_golden_pct.py` | Any change to what any check says about any fixture, under every profile it declares |
| `tests/test_repo_self_consistency.py` | A canonical version with no changelog entry; a shipping check with no spec; a summary check drifting onto an axis; a fixture the shipped schema rejects |
| `tests/test_readme_examples.py` | A README example that does not print what the README says it prints |
| `tests/test_audit_hotfix.py` | Every counter-example from the audit above |

The spec ratchet reports the real number: 12 of 17 shipping checks have no spec.
They are named in a backlog that may shrink and never grow.

---

## Measured

First profile adoption, on `flamehaven-audit-reports`. It declared eight surfaces
and invoked three; five were domain playbooks marked `on_demand`, 33,326 bytes
reaching no session at all.

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

---

## Known limits

| Item | State |
|---|---|
| Whether better context produces better work | Not measured. Needs sessions with a control |
| Profile adoption across live consumers | 1 of 6 |
| Handoff surface | Implemented; no consumer declares one |
| Spec coverage | 5 of 17 checks |
| `PCT-016` | Reserved, not implemented |
| `mica_spec` spread across consumers (`0.1.9`–`0.2.10`) | Not sought. Each package evolves on its own track; `PCT-006` reports the gap without prescribing convergence |

---

## Compatibility

Consumer packages written against `0.2.x` continue to resolve. `mica_core`
re-exports the primitive and evidence names it used to define, so a vendored
`tools/` copy keeps importing.

Two behaviours changed in ways a package can notice:

- A required layer with no usable `path` now fails `PCT-003`. A package relying
  on that being skipped was not resolving that surface in the first place.
- An empty `agent_context_surfaces` no longer falls back to every loaded surface.
  A package that declared it empty and expected everything delivered will now see
  an empty agent context, which is what it asked for.

`PCT-006` reports every `0.2.x` package as at least one major version behind
canonical. That is a report, not a requirement.

---

330+ tests. Python 3.9, 3.11, 3.12, 3.13. MIT.
