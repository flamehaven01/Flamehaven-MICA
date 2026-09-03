# v0.2.8 -> v0.2.9 Migration Guide

## Overview

Replace `tools/` and re-run the validator. That is the whole required migration.

A package that declares no memory profiles resolves exactly as it did under
v0.2.8. Everything new is opt-in.

There is **one behavioral change consumers must know about**, covered below.

---

## Required: replace the tool files

`tools/` gained four modules in this release. Copy the whole directory rather
than individual files.

```
tools/mica_core.py         <- replace
tools/mica_pct.py          <- replace
tools/mica_runtime.py      <- replace
tools/mica_invocation.py   <- replace
tools/mica_memory.py       <- replace
tools/mica_primitives.py   <- new
tools/mica_evidence.py     <- new
tools/mica_flow.py         <- new
tools/mica_measure.py      <- new
```

Then validate:

```bash
python tools/mica_pct.py .
```

Expected: the same contract result as before, now reported on three axes.

```text
Contract : CLOSED
Archive  : OK
Flow     : N/A

Overall: CLOSED CONTRACT
```

---

## Breaking: exit codes narrowed to the contract axis

`mica_pct.py` now exits 1 only when the **invocation contract** fails. Archive
quality and flow integrity report on their own axes without failing the run.

If your CI relied on exit 1 for an archive or flow failure — most commonly
`di_policy.critical_binding_required: true` escalating PCT-010 — add `--strict`:

```bash
python tools/mica_pct.py . --strict
```

| Situation | Default exit | `--strict` exit |
|---|---|---|
| Contract failure | 1 | 1 |
| Archive failure (e.g. unbound critical DI) | 0 | 1 |
| Flow failure (e.g. broken promotion provenance) | 0 | 1 |
| Invalid recorded invocation trace | 1 | 1 |

An invalid trace fails regardless of `--strict`: a corrupted capsule is bad
evidence about this package, not a quality signal.

---

## Optional: bump `mica_spec`

```yaml
mica_spec: "0.2.9"
```

Also update `mica_spec` in the archive JSON so PCT-006 sees them aligned.

Staying on `"0.2.8"` produces no warning — one patch behind is below the
threshold. Two or more behind warns.

---

## Optional: declare memory profiles

Without profiles, every session receives the same surfaces regardless of task.
Profiles let a review session and an incident session receive different memory.

```yaml
invocation_protocol:
  primary_pattern: readme_protocol
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

Rules the contract enforces:

- a requested profile must be declared
- every named surface must be a declared layer
- a profile must name at least one usable surface
- a profile must not repeat a surface
- `sections` may only slice a surface the profile actually invokes
- a requested section must exist in that file

Select one at the call site:

```bash
python tools/mica_runtime.py . --profile incident
python tools/mica_pct.py . --profile incident
```

If no profile is requested and a `default` profile exists, it applies.

**Do not let the model choose the profile.** Selection belongs to the operator
or to the hook that recognized the triggering event. A model that picks its own
memory reintroduces the circularity the invocation contract exists to remove.

---

## Optional: playbook sections

`sections` delivers named `##` sections instead of the whole file. The digest
recorded for that session covers the delivered slice, so drift is scoped to what
the session actually received — editing an undelivered section is not drift.

Section names are the heading text, matched exactly. Headings inside fenced code
blocks are content, not boundaries.

---

## Optional: archive freshness

```yaml
di_policy:
  max_archive_age_days: 180
```

| Context | Value |
|---|---|
| Active project | 90 |
| Maintenance mode | 180 |
| Stable / archived | 365 |

Requires `operation_meta.last_updated` in the archive as an ISO date.

---

## Checklist

- [ ] `tools/` replaced in full, including the four new modules
- [ ] `python tools/mica_pct.py .` returns the expected contract result
- [ ] CI relying on archive or flow failures updated to `--strict`
- [ ] (Optional) `mica_spec` bumped to `"0.2.9"` in mica.yaml and archive
- [ ] (Optional) `invocation_protocol.profiles` declared
- [ ] (Optional) `di_policy.max_archive_age_days` set
