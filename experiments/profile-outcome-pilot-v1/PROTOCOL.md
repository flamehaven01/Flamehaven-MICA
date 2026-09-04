# Profile Outcome Pilot v1 — Protocol

**Status: DRAFT. Not frozen. No task has been selected and nothing has been run.**

Every MICA release note carries the same sentence: whether better context
produces better work is not measured. This is the first attempt to measure it,
inside one consumer package, at a scale that can indicate a direction and
nothing more.

Freezing order, which this document is the first step of:

1. `PROTOCOL.md` — this file
2. `tasks.schema.json`
3. `allocation.schema.json`
4. review, then the real `tasks.json`
5. task prompt and base-commit digests recorded
6. randomisation seed generated, then the real `allocation.json`
7. execution

No task is selected, no consumer profile is modified, and no session is run
before step 6 is committed. The seed is generated *after* the tasks are frozen:
generating it earlier would allow choosing tasks with the allocation already
visible, which is the freedom this design exists to remove.

---

## What this can and cannot establish

**Can:** whether, within `flamehaven-audit-reports`, profile-selected context is
associated with a different rate of passing a pre-defined acceptance command
than loading every permitted surface.

**Cannot:** general performance of memory profiles, an effect size, anything
about other packages, or anything about other models. Six pairs cannot reach
statistical significance for any effect a reasonable person would call subtle.
A pilot answers whether an effect is large enough to be worth measuring
properly, not what the effect is.

The result is reported as a count, not a rate with a confidence interval.
If the two conditions differ on 0 or 1 of 6 tasks, the honest reading is "no
signal at this scale", not "no effect".

---

## Design

Paired replay. Each task is executed twice, once per condition, and the pair is
the unit of comparison.

| | |
|---|---|
| Consumer | `flamehaven-audit-reports` (the only package that declares profiles) |
| Tasks | 6 |
| Conditions | 2 |
| Sessions | 12 |
| Unit of analysis | the task pair |

### The two conditions

Everything is identical between them except which surfaces reach the agent.

- **A — load-everything.** All seven surfaces permitted by
  `agent_context_surfaces` are delivered. Measured previously at 61,525 bytes.
- **B — profile.** The task's declared profile is delivered. The profile is
  named in `tasks.json` per task and is not chosen during execution.

Everything else is held constant: same model, same prompt text, same tool set,
same time limit, same base commit, same acceptance command.

### Isolation

Each session gets:

- its own git worktree from the same frozen base commit
- its own session id
- its own output directory
- no shared scratch path

**Memory writes are disabled. The handoff surface is disabled.** Without this a
session leaves state that the next one reads, and the pairs stop being
independent. This is enforced by configuration, not by asking the session not
to write.

### Randomisation

For each task, which condition runs first is decided by the seed recorded in
`allocation.json`. Both orders appear across the six tasks. This controls for
anything that depends on execution order rather than condition.

The seed is generated once, after tasks are frozen, and recorded. A re-roll
after seeing any result invalidates the pilot.

---

## Task eligibility

A task may enter `tasks.json` only if all of these hold. These are criteria, not
a list of tasks; no task has been selected.

1. **A machine-checkable acceptance command exists.** A command that exits 0 or
   non-zero. No human judgement decides the primary outcome. If a candidate task
   has no such command, it is not eligible, however interesting it is.
2. **The acceptance command is written before the task is run**, and does not
   change between the two conditions.
3. **The allowed change paths are declared in advance.** Anything the task is
   permitted to modify. Changes outside them count as unnecessary changes, and
   a change outside them that is required to pass acceptance means the task was
   specified wrong and is excluded.
4. **The task is plausibly sensitive to which memory a session receives.** A
   task no context could help does not test anything. This is a judgement made
   at selection time and recorded per task with a one-line reason.
5. **The task is completable inside the time limit** by a session in either
   condition, judged from the task's shape rather than from a trial run. A
   trial run would leak the answer.

---

## Outcomes

### Primary

**Did the acceptance command pass.** Binary, per session, machine-judged.

Reported as a 6-row table of (task, A result, B result). No aggregate score.

### Secondary

Recorded for every session, and interpreted only as description:

| | |
|---|---|
| `agent_context_bytes` | from `mica_measure`, per condition |
| `tool_calls` | count |
| `elapsed_seconds` | wall clock |
| `unnecessary_changes` | files touched outside the declared allowed paths |

Secondary outcomes do not decide anything. A condition that passes acceptance
with more tool calls has still passed acceptance. They are recorded because a
large difference in them is worth noticing even when the primary outcome is
identical, and because the pilot's purpose is deciding what to measure next.

`unnecessary_changes` is the one secondary outcome that involves judgement about
quality. Where the diff is reviewed by a person, condition labels are hidden
during review. Where that is not practical, the count is reported as a raw file
count with no quality claim attached.

---

## Abort, exclude, re-run

**Abort the pilot** if the base commit changes, the consumer package changes, or
the protocol changes after step 6. Any of these ends this pilot; a changed
design is a new pilot with a new version directory.

**Exclude a task**, recording the reason, if:

- the acceptance command fails in both conditions for a reason unrelated to
  context (a broken environment, a network dependency, a flaky command)
- passing acceptance requires changing a path outside the declared allowed paths
- the session cannot start for infrastructure reasons

An excluded task is excluded as a pair. Excluding one condition's session and
keeping the other breaks the pairing.

**Re-run a session** only when it did not execute: a crash before the first tool
call, an infrastructure failure, an interrupted run. A session that executed and
produced a result is never re-run, whatever the result. Re-running a session
because its result was unwelcome is the failure mode this rule exists for.

Every abort, exclusion and re-run is recorded in `results.jsonl` with its reason
at the time it happened, not reconstructed afterwards.

---

## Recording

`results.jsonl`, one line per session, appended as it completes. Written during
the run, not assembled at the end.

`REPORT.md` is written after all sessions complete and records the 6-row primary
table, the secondary table, every exclusion with its reason, and what the result
does not establish. It is written whether the result is interesting or not: a
pilot that finds nothing is a result, and not publishing it would make every
later pilot's result unreadable.

---

## What would make this pilot wrong

Recorded now so it cannot be rationalised later.

- Choosing tasks after seeing the allocation
- Re-rolling the seed
- Re-running a session that produced an unwelcome result
- Changing an acceptance command after a session has run against it
- Reading a 6-pair difference as an effect size
- Reporting only the tasks where the conditions differed
- Treating `agent_context_bytes` as an outcome rather than a description of the
  condition. Fewer bytes is what condition B *is*, not evidence that it worked
